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


def layers_to_geotiff(dest_dir):
    for tt in range(0, 2401, 100):
        hour = '{:02d}'.format(tt // 100)
        minute = '{:02d}'.format(tt % 100)
        base_name = f'{RADIATION_LAYER_PREFIX}_{hour}.{minute}'
        layer_name = f'{base_name}@{GRASS_MAPSET}'
        file_name = os.path.join(dest_dir, f'{base_name}.tif')
        logger.info(f'Saving "{layer_name}" as "{file_name}"')
        subprocess.run(['grass', '--exec', 'r.out.gdal', f'input={layer_name}',
            f'output={file_name}', 'format=GTiff', '-c', '--overwrite'])

