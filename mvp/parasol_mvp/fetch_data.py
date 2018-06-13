"""
Utilities for retrieving data for parasol app
"""

from pkg_resources import resource_filename
import json
import os
import logging
import wget


# constants
PARASOL_HOME = os.path.expanduser(os.path.join('~', '.parasol_mvp'))
PARASOL_LIDAR = os.path.join(PARASOL_HOME, 'lidar')
LIDAR_URLS_FILE = resource_filename('parasol_mvp', 'lidar.json')

# init logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def get_lidar():
    """
    Download LiDAR tiles for the Parasol study area
    """
    # get tile urls
    with open(LIDAR_URLS_FILE, 'r') as fp:
        lidar_urls = json.load(fp)

    # create output folder if needed
    if not os.path.isdir(PARASOL_LIDAR):
        logger.info(f'Created directory {PARASOL_LIDAR}')
        os.makedirs(PARASOL_LIDAR)
   
    # download all tiles, skip if they exist 
    for url in lidar_urls:
        file_name = os.path.join(PARASOL_LIDAR, os.path.basename(url))
        if os.path.isfile(file_name):
            logging.info(f'LiDAR file {file_name} exists, skipping download')
        else:
            logging.info(f'Downloading LiDAR file {url}')
            wget.download(url, out=file_name)


def get_osm():
    """
    Download OpenStreetMaps data for the Parasol study area
    """
    raise NotImplementedError


# DEBUG - DELETE WHEN COMPLETED
if __name__ == '__main__':
    get_lidar()
