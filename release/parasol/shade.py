"""
Shade data handlers
"""

import os
import subprocess
import logging

from parasol import raster
from parasol import GRASS_MAPSET


logger = logging.getLogger(__name__)


# constants
INSOLATION_PREFIX = 'sol'
START_HOUR = 0
STOP_HOUR = 24
INTERVAL = 1


# TODO: use a temporary directory for scratch files
def insolation(x_min, x_max, y_min, y_max, year, day):
    
    # import surface elevation
    # TODO: read ground as well to compute constant shade component
    raster.retrieve(x_min, x_max, y_min, y_max, kind='surface',
        filename='surface.tif', plot=False)
    subprocess.run(['grass', '--exec', 'r.import', '--overwrite', 
        f'input=surface.tif', f'output=surface@{GRASS_MAPSET}']) 

    # set compute region -- very important!
    subprocess.run(['g.region', f'raster=surface@{GRASS_MAPSET}']) 

    # generate ancillary inputs needed for solar calc
    subprocess.run(['grass', '--exec', 'r.slope.aspect', '--overwrite',
        f'elevation=surface@{GRASS_MAPSET}', 'slope=slope', f'aspect=aspect'])
    subprocess.run(['grass', '--exec', 'r.latlong', '--overwrite',
        f'input=surface@{GRASS_MAPSET}', 'output=lat'])              
    subprocess.run(['grass', '--exec', 'r.latlong', '--overwrite', 
        f'input=surface@{GRASS_MAPSET}', '-l', 'output=lon'])              

    # solar calculation (loops over all intervals)
    subprocess.run(['grass', '--exec', 'r.sun.hourly', 
        f'elevation=surface@{GRASS_MAPSET}', f'aspect=aspect@{GRASS_MAPSET}',
        f'slope=slope@{GRASS_MAPSET}', f'start_time={START_HOUR}',
        f'end_time={STOP_HOUR}', f'time_step={INTERVAL}', f'day={day}',
        f'year={year}', f'glob_rad_basename={INSOLATION_PREFIX}', '--overwrite'])

    # build base names for layers and output files
    base_names = []
    for tt in range(START_HOUR*100, STOP_HOUR*100 + 1, int(INTERVAL*100)):
        hour = '{:02d}'.format(tt // 100)
        minute = '{:02d}'.format(tt % 100)
        base_names.append(f'{INSOLATION_PREFIX}_{hour}.{minute}')
    
    # dump insolation layers to file
    for base_name in base_names:
        layer_name = f'{base_name}@{GRASS_MAPSET}'
        file_name = f'{base_name}.tif'
        logger.info(f'Saving "{layer_name}" as "{file_name}"')
        subprocess.run(['grass', '--exec', 'r.out.gdal', f'input={layer_name}',
            f'output={file_name}', 'format=GTiff', '-c', '--overwrite'])


# # NOTE: command works Bash, fails to find files here. Shelved as non-essential
# def clear_mapset():
#     subprocess.run(['grass', '--exec', 'g.remove', 'type=raster', f'pattern="*"'])

