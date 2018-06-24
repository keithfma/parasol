"""
Shade data handlers
"""

import os
import subprocess
import logging

from parasol import surface, common, cfg


logger = logging.getLogger(__name__)


# constants
PREFIX = 'sol'

# # setup environment variables for GRASS
# os.environ['GISBASE'] = GRASS_GISBASE
# os.environ['GISRC'] = GRASS_GISRC
# 
# # create grass configuration directory, if needed
# if not os.path.isdir(os.path.dirname(GRASS_GISRC)):
#     os.makedirs(os.path.dirname(GRASS_GISRC))
# 
# # create grass configuration file
# with open(GRASS_GISRC, 'w') as fp:
#     fp.write(f'GISDBASE: {GRASS_GISDBASE}\n')
#     fp.write(f'LOCATION_NAME: {GRASS_LOCATION}\n')
#     fp.write(f'MAPSET: {GRASS_MAPSET}\n')
#     fp.write('GUI: wxpython\n')
# 
# # create database, location, and mapset folders, if needed
# map_dir = f'{GRASS_GISDBASE}/{GRASS_LOCATION}/{GRASS_MAPSET}'
# if not os.path.isdir(map_dir):
#     os.makedirs(map_dir)
#     subprocess.run(['grass74', '-c', f'EPSG:{PRJ_SRID}', '-e', map_dir])


# TODO: work on tiles, then merge. Will be necessary for larger input areas
def insolation(year, day):
    """
    Compute insolation (W/m2) raster within ROI for defined interval
    
    Arguments:
        x_min, x_max, y_min, y_max: floats, limits of ROI
        year, day: ints, date for insolation calculation
        prefix: string, base name for resulting geotiffs, generates one geotiff
            per timestep
    """
    
    # import surface and ground elevations
    surf_file = os.path.join(cfg.SURFACE_DIR, 'surface.tif')
    subprocess.run(['grass', '--exec', 'r.import', '--overwrite', 
        f'input={surf_file}', f'output=surface@{GRASS_MAPSET}']) 

    grnd_file = os.path.join(cfg.SURFACE_DIR, 'ground.tif')
    subprocess.run(['grass', '--exec', 'r.import', '--overwrite', 
        f'input={grnd_file}', f'output=ground@{GRASS_MAPSET}']) 

    # set compute region -- very important!
    subprocess.run(['g.region', f'raster=surface@{GRASS_MAPSET}']) 

    # # generate ancillary inputs needed for solar calc
    # subprocess.run(['grass', '--exec', 'r.slope.aspect', '--overwrite',
    #     f'elevation=surface@{GRASS_MAPSET}', 'slope=slope', f'aspect=aspect'])
    # subprocess.run(['grass', '--exec', 'r.latlong', '--overwrite',
    #     f'input=surface@{GRASS_MAPSET}', 'output=lat'])              
    # subprocess.run(['grass', '--exec', 'r.latlong', '--overwrite', 
    #     f'input=surface@{GRASS_MAPSET}', '-l', 'output=lon'])              

    # # solar calculation (loops over all intervals)
    # subprocess.run(['grass', '--exec', 'r.sun.hourly', 
    #     f'elevation=surface@{GRASS_MAPSET}', f'aspect=aspect@{GRASS_MAPSET}',
    #     f'slope=slope@{GRASS_MAPSET}', f'start_time={SHADE_START_HOUR}',
    #     f'end_time={SHADE_STOP_HOUR}', f'time_step={SHADE_INTERVAL_HOUR}', f'day={day}',
    #     f'year={year}', f'glob_rad_basename={PREFIX}', '--overwrite'])

    # # build base names for layers and output files
    # base_names = []
    # for tt in range(SHADE_START_HOUR*100, SHADE_STOP_HOUR*100 + 1, int(SHADE_INTERVAL_HOUR*100)):
    #     hour = '{:02d}'.format(tt // 100)
    #     minute = '{:02d}'.format(tt % 100)
    #     base_names.append(f'{PREFIX}_{hour}.{minute}')
    # 
    # # dump insolation layers to file
    # for base_name in base_names:
    #     layer_name = f'{base_name}@{GRASS_MAPSET}'
    #     file_name = os.path.join(DATA_DIR, f'{base_name}.tif')
    #     logger.info(f'Saving "{layer_name}" as "{file_name}"')
    #     subprocess.run(['grass', '--exec', 'r.out.gdal', f'input={layer_name}',
    #         f'output={file_name}', 'format=GTiff', '-c', '--overwrite'])


# # NOTE: command works Bash, fails to find files here. Shelved as non-essential
# def clear_mapset():
#     subprocess.run(['grass', '--exec', 'g.remove', 'type=raster', f'pattern="*"'])


