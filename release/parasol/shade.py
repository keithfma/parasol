"""
Shade data handlers
"""

import os
import subprocess
import logging
import argparse
from datetime import datetime

from parasol import surface, common, cfg


logger = logging.getLogger(__name__)


# constants
PREFIX = 'sol'


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


# TODO: switch to a single time calculation, if you can


# TODO: work on tiles, then merge. Will be necessary for larger input areas
def insolation(year=None, day=None, hour_start=cfg.SHADE_START_HOUR,
    hour_stop=cfg.SHADE_STOP_HOUR, hour_interval=cfg.SHADE_INTERVAL_HOUR,
    prefix='today'):
    """
    Compute insolation (W/m2) raster within ROI for defined interval
    
    Arguments:
        year, day: ints, date for insolation calculation
        hour_start, hour_stop: floats, start and end hours for loop
        hour_interval: float, step size for loop
        prefix: string, base name for resulting geotiffs, generates one geotiff
            per timestep
    """
    # check arguments
    if round(hour_interval*100) != hour_interval*100:
        raise ValueError('"hour_interval" precision is limited to 0.01')

    # use current day as default time
    now = datetime.now()
    if not year:
        year = now.year
    if not day:
        day = int(now.strftime('%j'))

    # create output directory, if needed
    if not os.path.isdir(cfg.SHADE_DIR):
        os.makedirs(cfg.SHADE_DIR)

    # set compute region -- very important!
    subprocess.run(['g.region', f'raster=surface@{cfg.GRASS_MAPSET}']) 

    # solar calculation (loops over all intervals)
    subprocess.run(['grass', '--exec', 'r.sun.hourly', 
        f'elevation=surface@{cfg.GRASS_MAPSET}', f'aspect=aspect@{cfg.GRASS_MAPSET}',
        f'slope=slope@{cfg.GRASS_MAPSET}', f'start_time={hour_start}',
        f'end_time={hour_stop}', f'time_step={hour_interval}', f'day={day}',
        f'year={year}', f'glob_rad_basename={prefix}', '--overwrite'])

    # build base names for layers
    base_names = []
    for tt in range(hour_start*100, hour_stop*100 + 1, int(hour_interval*100)):
        hour = '{:02d}'.format(tt // 100)
        minute = '{:02d}'.format(tt % 100)
        base_names.append(f'{prefix}_{hour}.{minute}')
    
    # dump insolation layers to file
    for base_name in base_names:
        layer_name = f'{base_name}@{cfg.GRASS_MAPSET}'
        file_name = os.path.join(cfg.SHADE_DIR, f'{base_name}.tif')
        logger.info(f'Saving "{layer_name}" as "{file_name}"')
        subprocess.run(['grass', '--exec', 'r.out.gdal', f'input={layer_name}',
            f'output={file_name}', 'format=GTiff', '-c', '--overwrite'])




# command line utilities -----------------------------------------------------


def initialize_cli():
    """Command line utility to initsurface/ground data and display layers"""
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
    # TODO: compute current day shade 
    # TODO: compute past shade for validation images 
