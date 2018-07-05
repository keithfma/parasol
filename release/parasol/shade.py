"""
Shade data handlers
"""

import os
import subprocess
import logging
import argparse
from datetime import datetime
import numpy as np
import math
from pdb import set_trace
import requests
from pkg_resources import resource_filename
import glob
from osgeo import gdal

from parasol import surface, common, cfg


logger = logging.getLogger(__name__)


def init_grass():
    """Jump through all the hoops needed to run GRASS programatically"""

    # set required environment variables
    os.environ['GISBASE'] = cfg.GRASS_GISBASE
    os.environ['GISRC'] = cfg.GRASS_GISRC
    
    # create grass configuration directory, if needed
    if not os.path.isdir(os.path.dirname(cfg.GRASS_GISRC)):
        os.makedirs(os.path.dirname(cfg.GRASS_GISRC))
    
    # create grass configuration file
    with open(cfg.GRASS_GISRC, 'w') as fp:
        fp.write(f'GISDBASE: {cfg.GRASS_GISDBASE}\n')
        fp.write(f'LOCATION_NAME: {cfg.GRASS_LOCATION}\n')
        fp.write(f'MAPSET: {cfg.GRASS_MAPSET}\n')
        fp.write('GUI: wxpython\n')
    
    # # create database, location, and mapset folders, if needed
    if not os.path.isdir(cfg.GRASS_GISDBASE):
        os.makedirs(cfg.GRASS_GISDBASE)
    map_dir = f'{cfg.GRASS_GISDBASE}/{cfg.GRASS_LOCATION}/{cfg.GRASS_MAPSET}'
    subprocess.run(['grass74', '-c', f'EPSG:{cfg.PRJ_SRID}', '-e', map_dir])


def clear_grass():
    """Remove all working files from the GRASS database"""
    # subprocess.run(['grass', '--exec', 'g.remove', 'type=raster', f'pattern="*"'])
    raise NotImplementedError # works in Bash, fails to find files here, shelved as non-essential


def prep_inputs():
    """Prepare static inputs for insolation calculation in GRASS database"""
    
    # import surface and ground elevations
    surf_file = os.path.join(cfg.SURFACE_DIR, 'surface.tif')
    subprocess.run(['grass', '--exec', 'r.import', '--overwrite', 
        f'input={surf_file}', f'output=surface@{cfg.GRASS_MAPSET}']) 

    grnd_file = os.path.join(cfg.SURFACE_DIR, 'ground.tif')
    subprocess.run(['grass', '--exec', 'r.import', '--overwrite', 
        f'input={grnd_file}', f'output=ground@{cfg.GRASS_MAPSET}']) 

    # set compute region -- very important!
    subprocess.run(['g.region', f'raster=surface@{cfg.GRASS_MAPSET}']) 
    
    # compute constant shade component (e.g., under trees, within buildings
    mapcalc_expression = f'"shade-mask@{cfg.GRASS_MAPSET}" = ("surface@{cfg.GRASS_MAPSET}"-"ground@{cfg.GRASS_MAPSET}")>3'
    subprocess.run(['r.mapcalc', f'expression={mapcalc_expression}', '--overwrite'])

    # generate ancillary inputs needed for solar calc
    subprocess.run(['grass', '--exec', 'r.slope.aspect', '--overwrite',
        f'elevation=surface@{cfg.GRASS_MAPSET}', 'slope=slope', f'aspect=aspect'])
    subprocess.run(['grass', '--exec', 'r.latlong', '--overwrite',
        f'input=surface@{cfg.GRASS_MAPSET}', 'output=lat'])              
    subprocess.run(['grass', '--exec', 'r.latlong', '--overwrite', 
        f'input=surface@{cfg.GRASS_MAPSET}', '-l', 'output=lon'])              


# TODO: save insolation on upper surface and lower surface, the former is better for visualization
def insolation(day, hour, top_name, bot_name):
    """
    Compute insolation (W/m2) raster within ROI for specified time 
    
    Arguments:
        day: int, day of the year 
        hour: local solar time, decimal hours
        top_name: string, path to save retults as geotiff
        bot_name: string, path to save retults as geotiff
    """
    # get name for GRASS layer
    top_layer = os.path.splitext(os.path.basename(top_name))[0]
    bot_layer = os.path.splitext(os.path.basename(bot_name))[0]

    # set compute region -- very important!
    subprocess.run(['g.region', f'raster=surface@{cfg.GRASS_MAPSET}']) 

    # solar calculation
    logger.info(f'Computing insolation for day={day}, time={hour}')
    subprocess.run(['grass', '--exec', 'r.sun', f'time={hour}', f'day={day}',
        f'elevation=surface@{cfg.GRASS_MAPSET}', f'aspect=aspect@{cfg.GRASS_MAPSET}',
        f'slope=slope@{cfg.GRASS_MAPSET}', f'glob_rad={top_layer}@{cfg.GRASS_MAPSET}',
        '--overwrite'])

    # compute minimum insolation
    result = subprocess.run(['grass', '--exec', 'r.info', '-r',
        f'map={top_layer}@{cfg.GRASS_MAPSET}'], stdout=subprocess.PIPE)
    min_line = result.stdout.decode('utf-8').split()[0]
    min_value = float(min_line.split('=')[1])

    # apply minimum insolation where surface is above the ground (trees, buildings)
    if_str = f'if( "shade-mask", {min_value}, "{top_layer}@{cfg.GRASS_MAPSET}" )'
    subprocess.run(['grass', '--exec', 'r.mapcalc', f'expression="{bot_layer}@{cfg.GRASS_MAPSET}" = {if_str}', '--overwrite'])

    # dump results to file
    logger.info(f'Saving top surface insolation as "{top_name}"')
    subprocess.run(['grass', '--exec', 'r.out.gdal', f'input={top_layer}@{cfg.GRASS_MAPSET}',
        f'output={top_name}', 'format=GTiff', '-c', '--overwrite'])
    logger.info(f'Saving ground surface insolation as "{bot_name}"')
    subprocess.run(['grass', '--exec', 'r.out.gdal', f'input={bot_layer}@{cfg.GRASS_MAPSET}',
        f'output={bot_name}', 'format=GTiff', '-c', '--overwrite'])
    
    # delete the temporary layer in the GRASS DB
    # TODO: fails to find layer, not clear why
    subprocess.run(['grass', '--exec', 'g.remove', '-f', 'type=raster',
        f'pattern="{top_layer}"'])
    subprocess.run(['grass', '--exec', 'g.remove', '-f', 'type=raster',
        f'pattern="{bot_layer}"'])


# TODO: explore multiprocessing
def update_today():
    """Update insolation frames for whole day in loop"""

    # get current day and list of times (interval, etc, are set using config variables)
    # TODO: use common.shade_meta()
    day = int(datetime.now().strftime('%j'))
    times = np.arange(cfg.SHADE_START_HOUR, cfg.SHADE_STOP_HOUR, cfg.SHADE_INTERVAL_HOUR)
    
    # create output directory, if needed
    if not os.path.isdir(cfg.SHADE_DIR):
        os.makedirs(cfg.SHADE_DIR)

    # TODO: use common.shade_meta()
    for ii, time in enumerate(times): 
        logger.info(f'Update daily insolation, time step {ii} of {len(times)}')
        time_hour = int(math.floor(time))
        time_min = int(round((time - time_hour)*60))
        top_name = os.path.join(cfg.SHADE_DIR,
            f'{cfg.SHADE_TOP_PREFIX}{time_hour:02d}{time_min:02d}.tif')
        bot_name = os.path.join(cfg.SHADE_DIR,
            f'{cfg.SHADE_BOTTOM_PREFIX}{time_hour:02d}{time_min:02d}.tif')
        insolation(day, time, top_name, bot_name)


def retrieve(hour, minute, bbox=None):
    """
    Retrieve (subset of) insolation raster closest to the specified time

    Arguments:
        hour, min: floats, time to retrieve, day is assumed to be "today", if
            there is not an exact match, the nearest available raster will be
            returned
        bbox: length-5 tuple/list, [x_min, x_max, y_min, y_max, srid], bounding
            box used to clip raster, output may not match limits exactly 
    
    Returns: x_vec, y_vec, z_grd
        x_vec, y_vec: numpy 1D arrays, coordinate vectors
        z_grd: numpy 2D array, insolation
    """
    # handle bbox
    if bbox:
        raise NotImplementedError('Raster subsets are not yet supported')

    # select insolation raster file
    out_time = hour + minute/60
    shade_file = None
    shade_time = 99999
    for this_file in glob.glob(os.path.join(cfg.SHADE_DIR, 'today_*.tif')):
        tmp = os.path.basename(this_file)[6:-4]
        this_time = float(tmp[:2]) + float(tmp[2:])/60
        if abs(out_time - this_time) < abs(out_time - shade_time):
            shade_time = this_time
            shade_file = this_file 

    # read in raster (subset) and coordinate vectors
    # TODO: implement subset using bounding box
    ds = gdal.Open(shade_file)
    z_grd = np.array(ds.GetRasterBand(1).ReadAsArray())

    transform = ds.GetGeoTransform()
    y_pixel = np.arange(0, z_grd.shape[0])
    x_pixel = np.arange(0, z_grd.shape[1])
    x_vec = transform[0] + x_pixel*transform[1] + y_pixel*transform[2]
    y_vec = transform[3] + x_pixel*transform[4] + y_pixel*transform[5]

    return x_vec, y_vec, z_grd


# command line utilities -----------------------------------------------------


def initialize_cli():
    """Command line utility to init inputs for shade calculations"""
    ap = argparse.ArgumentParser(
        description="Initialize Parasol surface & ground raster databases - clobbers existing!",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter) 
    ap.add_argument('--log', type=str, default='info', help="select logging level",
                    choices=['debug', 'info', 'warning', 'error', 'critical'])
    args = ap.parse_args()

    log_lvl = getattr(logging, args.log.upper())
    logging.basicConfig(level=log_lvl)
    logger.setLevel(log_lvl)

    init_grass()
    prep_inputs()


def update_cli():
    """Command line utility to init inputs for shade calculations"""
    ap = argparse.ArgumentParser(
        description="Update daily insolation rasters - clobbers existing!",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter) 
    ap.add_argument('--log', type=str, default='info', help="select logging level",
                    choices=['debug', 'info', 'warning', 'error', 'critical'])
    args = ap.parse_args()

    log_lvl = getattr(logging, args.log.upper())
    logging.basicConfig(level=log_lvl)
    logger.setLevel(log_lvl)

    update_today()


# TODO: CLI for computing a validation scene


