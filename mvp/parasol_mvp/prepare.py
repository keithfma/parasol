"""
Utilities for preparing (retrieving, preprocessing) data for parasol app
"""

from pkg_resources import resource_filename
import json
import os
import logging
import wget
import requests
import pdal
import glob
import io
import subprocess


# constants
PARASOL_HOME = os.path.expanduser(os.path.join('~', '.parasol_mvp'))
PARASOL_LIDAR = os.path.join(PARASOL_HOME, 'lidar')
PARASOL_LIDAR_RAW = os.path.join(PARASOL_LIDAR, 'raw')
PARASOL_LIDAR_CLEAN = os.path.join(PARASOL_LIDAR, 'clean')
PARASOL_LIDAR_TOP = os.path.join(PARASOL_LIDAR, 'top')
PARASOL_LIDAR_TOP_DEM = os.path.join(PARASOL_LIDAR, 'top_dem')
PARASOL_LIDAR_BOTTOM = os.path.join(PARASOL_LIDAR, 'bottom')
PARASOL_LIDAR_BOTTOM_DEM = os.path.join(PARASOL_LIDAR, 'bottom_dem')
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
    if not os.path.isdir(PARASOL_LIDAR_RAW):
        logger.info(f'Created directory {PARASOL_LIDAR_RAW}')
        os.makedirs(PARASOL_LIDAR_RAW)
   
    # download all tiles, skip if they exist 
    for url in lidar_urls:
        file_name = os.path.join(PARASOL_LIDAR_RAW, os.path.basename(url))
        if os.path.isfile(file_name):
            logging.info(f'LiDAR file {file_name} exists, skipping download')
        else:
            logging.info(f'Downloading LiDAR file {url}')
            wget.download(url, out=file_name)


def lidar_preprocess_all():
    """
    Loop over all available lidar files, run preprocessing pipelines as needed
    """
    raw_files = glob.glob(os.path.join(PARASOL_LIDAR_RAW, '*.laz'))
    for raw_file in raw_files:
        lidar_preprocess(raw_file)


def lidar_preprocess(input_file):
    """
    Preprocess lidar data (downsample, filter outliers, decompose ground/canopy) 
    
    Arguments:
        input_file: string, path to input LAZ file containing raw LiDAR data
    
    Returns: Nothing, results are saved to disk, specifically:
        *_bot.laz, *_bot.tif:
        *_top.laz, *_top.tif:
    """
    # generate filenames for steps along pre-processing pipeline
    input_folder, input_name = os.path.split(input_file)
    input_base, input_ext = os.path.splitext(input_name)
    top_file        = os.path.join(PARASOL_LIDAR_TOP, f'{input_base}_top.laz')
    top_dem_file    = os.path.join(PARASOL_LIDAR_TOP_DEM, f'{input_base}_top.tif')
    bottom_file     = os.path.join(PARASOL_LIDAR_BOTTOM, f'{input_base}_bottom.laz')
    bottom_dem_file = os.path.join(PARASOL_LIDAR_BOTTOM_DEM, f'{input_base}_bottom.tif')
    
    # create output folders, if needed
    dir_names = [PARASOL_LIDAR_TOP, PARASOL_LIDAR_TOP_DEM,
                 PARASOL_LIDAR_BOTTOM, PARASOL_LIDAR_BOTTOM_DEM]
    for dir_name in dir_names:
        if not os.path.isdir(dir_name):
            logger.info(f'Created directory {dir_name}')
            os.makedirs(dir_name)

    # extract top surface points, if needed
    if os.path.isfile(top_file):
        logger.info(f'Top surface points file {top_file} exists, skipping')
    else:
        logger.info(f'Extracting top surface points: {input_file} -> {top_file}')
        top_pipeline = json.dumps({
            "pipeline": [
                {
                    "type": "readers.las",
                    "filename": input_file,
                },  
                {
                    "type":"filters.returns",
                    "groups":"first,only"
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
                    "filename": top_file,
                    "forward": "all",
                    "scale_x": "auto",
                    "scale_y": "auto",
                    "scale_z": "auto",
                    "offset_x": "auto",
                    "offset_y": "auto",
                    "offset_z": "auto",
                    "compression": "laszip"
                }
            ]
        })
        subprocess.run(
            ['pdal', 'pipeline', '--stdin'], input=top_pipeline, encoding='utf-8')
    
    # generate top raster
    if os.path.isfile(top_dem_file):
        logger.info(f'Top surface file {top_dem_file} exists, skipping')
    else:
        logger.info(f'Building top surface: {top_file} -> {top_dem_file}')
        top_dem_pipeline = json.dumps({
            "pipeline": [
                {
                    "type": "readers.las",
                    "filename": top_file,
                },
                {
                    "type": "writers.gdal", 
                    "filename": top_dem_file,
                    "resolution": 1.0, 
                    "window_size": 100.0,
                    "output_type": "idw", 
                    "dimension": "Z" 
                }
            ]
        })
        subprocess.run(
            ['pdal', 'pipeline', '--stdin', '--nostream'], input=top_dem_pipeline, encoding='utf-8')

    # TODO: nearest neighbor interp?


    # extract bottom surface points, if needed
    if os.path.isfile(bottom_file):
        logger.info(f'Bottom surface points file {bottom_file} exists, skipping')
    else:
        logger.info(f'Extracting bottom surface points: {input_file} -> {bottom_file}')
        bottom_pipeline = json.dumps({
            "pipeline": [
                {
                    "type": "readers.las",
                    "filename": input_file,
                },  
                {
                    "type":"filters.returns",
                    "groups":"last,only"
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
                    "type": "filters.pmf"
                },
                {
                    "type":"filters.range",
                    "limits":"Classification[2:2]"
                },
                {
                    "type": "writers.las", 
                    "filename": bottom_file,
                    "forward": "all",
                    "scale_x": "auto",
                    "scale_y": "auto",
                    "scale_z": "auto",
                    "offset_x": "auto",
                    "offset_y": "auto",
                    "offset_z": "auto",
                    "compression": "laszip"
                }
            ]
        })
        subprocess.run(
            ['pdal', 'pipeline', '--stdin'], input=bottom_pipeline, encoding='utf-8')

    # generate bottom raster, if needed
    if os.path.isfile(bottom_dem_file):
        logger.info(f'Bottom surface file {bottom_dem_file} exists, skipping')
    else:
        logger.info(f'Building bottom surface: {bottom_file} -> {bottom_dem_file}')
        bottom_dem_pipeline = json.dumps({
            "pipeline": [
                {
                    "type": "readers.las",
                    "filename": bottom_file,
                },
                {
                    "type": "writers.gdal", 
                    "filename": bottom_dem_file,
                    "resolution": 1.0, 
                    "window_size": 100.0,
                    "output_type": "idw", 
                    "dimension": "Z" 
                }
            ]
        })
        subprocess.run(
            ['pdal', 'pipeline', '--stdin', '--nostream'], input=bottom_dem_pipeline, encoding='utf-8')

    # TODO: nearest neighbor interp?

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

