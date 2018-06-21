"""
Shade data handlers
"""

import os
import subprocess
import logging

from parasol import GRASS_MAPSET


logger = logging.getLogger(__name__)


# constants
RADIATION_LAYER_PREFIX = 'radiation'


def sun_base_names(start_hour, stop_hour, interval):
    """
    Return list of time strings, as used by GRASS sun.hourly

    Arguments:
        start_hour: integer, range 0-24
        stop_hour: integer, range 0-24
        interval: float, decimal hour
    
    Return: list of strings
    """
    base_names = []
    for tt in range(start_hour*100, stop_hour*100 + 1, int(interval*100)):
        hour = '{:02d}'.format(tt // 100)
        minute = '{:02d}'.format(tt % 100)
        base_names.append(f'{RADIATION_LAYER_PREFIX}_{hour}.{minute}')
    return base_names


def layers_to_geotiff(dest_dir):
    """
    Write out GRASS radiation layers to local geotiff files

    Arguments:
        dest_dir: string, destination folder to save files to

    Returns: Nothing
    """
    for base_name in sun_base_names(0, 24, 1):
        layer_name = f'{base_name}@{GRASS_MAPSET}'
        file_name = os.path.join(dest_dir, f'{base_name}.tif')
        logger.info(f'Saving "{layer_name}" as "{file_name}"')
        subprocess.run(['grass', '--exec', 'r.out.gdal', f'input={layer_name}',
            f'output={file_name}', 'format=GTiff', '-c', '--overwrite'])

