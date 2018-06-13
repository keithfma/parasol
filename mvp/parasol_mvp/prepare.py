"""
Utilities for retrieving data for parasol app
"""

from pkg_resources import resource_filename
import json
import os
import logging
import wget
import requests


# constants
PARASOL_HOME = os.path.expanduser(os.path.join('~', '.parasol_mvp'))
PARASOL_LIDAR = os.path.join(PARASOL_HOME, 'lidar')
PARASOL_OSM = os.path.join(PARASOL_HOME, 'osm')
LIDAR_URLS_FILE = resource_filename('parasol_mvp', 'lidar.json')
OSM_BBOX_FILE = resource_filename('parasol_mvp', 'osm.json')

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


def lidar_preprocess(input_file):
    """
    Preprocess lidar data (downsample, filter outliers, decompose ground/canopy) 
    
    Arguments:
        input_file: string, path to input LAZ file containing raw LiDAR data
    
    Returns: Nothing, results are saved to disk
    """
    raise NotImplementedError


def get_osm():
    """
    Download OpenStreetMaps data for the Parasol study area
    """
    # get OSM bounding box (geographic)
    with open(OSM_BBOX_FILE, 'r') as fp:
        bbox = json.load(fp)

    # create output folder if needed
    if not os.path.isdir(PARASOL_OSM):
        logger.info(f'Created directory {PARASOL_OSM}')
        os.makedirs(PARASOL_OSM)

    # fetch data from OSM overpass API
    # ...cribbed example from: https://github.com/pgRouting/osm2pgrouting/issues/44
    file_name = os.path.join(PARASOL_OSM, 'all.osm')
    bbox_str = '{lon_min},{lat_min},{lon_max},{lat_max}'.format(**bbox)
    url = f'http://www.overpass-api.de/api/xapi?*[bbox={bbox_str}][@meta]'
    print(url)
    wget.download(url, out=file_name)


    # BBOX="-122.8,45.4,-122.5,45.6"
    # wget --progress=dot:mega -O "sampledata.osm" "http://www.overpass-api.de/api/xapi?*[bbox=${BBOX}][@meta]"


# DEBUG - DELETE WHEN COMPLETED
if __name__ == '__main__':
    get_osm()
