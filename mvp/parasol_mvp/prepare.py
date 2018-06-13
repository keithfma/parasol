"""
Utilities for retrieving data for parasol app
"""

from pkg_resources import resource_filename
import json
import os
import logging
import wget
import requests
import pdal


# constants
PARASOL_HOME = os.path.expanduser(os.path.join('~', '.parasol_mvp'))
PARASOL_LIDAR = os.path.join(PARASOL_HOME, 'lidar')
PARASOL_OSM = os.path.join(PARASOL_HOME, 'osm')
PARASOL_PROJ_SRS = "EPSG:32619" 
PARASOL_GEOG_SRS = "EPSG:4269" 
LIDAR_URLS_FILE = resource_filename('parasol_mvp', 'lidar.json')
OSM_BBOX_FILE = resource_filename('parasol_mvp', 'osm.json')

# init logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# LiDAR ----------------------------------------------------------------------


def lidar_fetch():
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


def lidar_preprocess_all():
    """
    Loop over all available lidar files, run preprocessing pipelines as needed
    """
    # DEBUG: hard-code one
    raw_files = ['/home/keith/.parasol_mvp/lidar/20131208_usgspostsandy_19TCG270920.laz']
    raise NotImplementedError


def lidar_preprocess(input_file):
    """
    Preprocess lidar data (downsample, filter outliers, decompose ground/canopy) 
    
    Arguments:
        input_file: string, path to input LAZ file containing raw LiDAR data
    
    Returns: Nothing, results are saved to disk, specifically:
        *_clean.laz:
        *_bot.laz, *_bot.tif:
        *_top.laz, *_top.tif:
    """
    # generate filenames for steps along pre-processing pipeline
    input_base, input_ext = os.path.splitext(input_file)
    clean_file = f'{base}_clean.laz'

    # clean input file, if needed
    if os.path.isfile(clean_file):
        logger.info(f'Clean file {clean_file} exists, skipping')
    else:
        clean_pipeline_def = {
            "pipeline": [
                {
                    "type": "readers.las",
                    "filename": input_file,
                },  
                {
                    "type": "filters.reprojection",
                    "out_srs": PARASOL_PROJ_SRS,
                },
                {
                    "type":"filters.voxelgrid",
                    "leaf_x": 1.0,
                    "leaf_y": 1.0,
                    "leaf_z": 1.0,
                },
                {
                    "type": "filters.outlier",
                    "method": "statistical",
                    "mean_k": 12,
                    "multiplier": 2.2
                },
                {
                    "type":"filters.range",
                    "limits":"Classification![7:7]"
                },
                {
                    "type": "writers.las", 
                    "filename": clean_file,
                    "a_srs": "EPSG:32619", 
                    "scale_x": "auto",
                    "scale_y": "auto",
                    "scale_z": "auto",
                    "offset_x": "auto",
                    "offset_y": "auto",
                    "offset_z": "auto",
                    "compression": "laszip"
                }
            ]
        }
        clean_pipeline = pdal.Pipeline(json.dumps(clean_pipeline_def))
        clean_pipeline.validate()
        clean_pipeline.loglevel = 8 #really noisy
        pipeline.execute()


# OSM ------------------------------------------------------------------------


def osm_fetch():
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
    logger.info(f'Downloading OSM data from: {url}')
    wget.download(url, out=file_name)

