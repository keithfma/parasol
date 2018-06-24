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


def insolation(day, hour, file_name):
    """
    Compute insolation (W/m2) raster within ROI for specified time 
    
    Arguments:
        day: int, day of the year 
        hour: local solar time, decimal hours
        file_name: string, path to save retults as geotiff
    """
    # get name for GRASS layer
    base_name = os.path.splitext(os.path.basename(file_name))[0]
    layer_name = f'{base_name}{cfg.GRASS_MAPSET}'

    # set compute region -- very important!
    subprocess.run(['g.region', f'raster=surface@{cfg.GRASS_MAPSET}']) 

    # solar calculation
    subprocess.run(['grass', '--exec', 'r.sun', f'time={hour}', f'day={day}',
        f'elevation=surface@{cfg.GRASS_MAPSET}', f'aspect=aspect@{cfg.GRASS_MAPSET}',
        f'slope=slope@{cfg.GRASS_MAPSET}', f'glob_rad={layer_name}',
        '--overwrite'])

    # dump results to file
    logger.info(f'Saving "{layer_name}" as "{file_name}"')
    subprocess.run(['grass', '--exec', 'r.out.gdal', f'input={layer_name}',
        f'output={file_name}', 'format=GTiff', '-c', '--overwrite'])
    
    # # delete the temporary layer in the GRASS DB
    # subprocess.run(['grass', '--exec', 'g.remove', '-f', 'type=raster',
    #     f'pattern={layer_name}'])


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

# TODO: CLI for computing a validation scene

# TODO: CLI for updating shade for current day (multithread?)
