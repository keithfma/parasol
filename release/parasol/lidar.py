"""
LiDAR data handlers
"""

import psycopg2 as pg 
import subprocess
import json
import pdal
import argparse
from glob import glob
import logging
import numpy as np
from scipy.spatial import cKDTree
import math

from parasol import LIDAR_DB, LIDAR_TABLE, LIDAR_GEO_SRID, LIDAR_PRJ_SRID, \
    PSQL_USER, PSQL_PASS, PSQL_HOST, PSQL_PORT

# DEBUG ONLY
from matplotlib import pyplot as plt


logger = logging.getLogger(__name__)


def connect_db(dbname=LIDAR_DB):
    """
    Return connection to lidar DB and return cursor

    Arguments:
        dbname: string, database name to connect to

    Returns: psycopg2 connection object
    """
    conn = pg.connect(dbname=dbname, user=PSQL_USER, password=PSQL_PASS,
        host=PSQL_HOST, port=PSQL_PORT)
    return conn
    

def create_db(clobber=False):
    """
    Create a new database and initialize for lidar point data

    Arguments:
        clobber: set True to delete and re-initialize an existing database

    Return: Nothing
    """
    # TODO: add indexes as needed
    # connect to default database
    with connect_db('postgres') as conn:
        conn.set_isolation_level(pg.extensions.ISOLATION_LEVEL_AUTOCOMMIT) 
        cur = conn.cursor()
        if clobber:
            logger.info(f'Dropped existing database: {LIDAR_DB} @ {PSQL_HOST}:{PSQL_PORT}')
            cur.execute(f'DROP DATABASE IF EXISTS {LIDAR_DB}');
        cur.execute(f'CREATE DATABASE {LIDAR_DB};')
    # init new database
    with connect_db() as conn:
        cur = conn.cursor()
        cur.execute('CREATE EXTENSION postgis;')
        cur.execute('CREATE EXTENSION pointcloud;')
        cur.execute('CREATE EXTENSION pointcloud_postgis;')
        cur.execute(f'CREATE TABLE {LIDAR_TABLE} (id SERIAL PRIMARY KEY, pa PCPATCH(1));')
    logger.info(f'Created new database: {LIDAR_DB} @ {PSQL_HOST}:{PSQL_PORT}')


def ingest(laz_file):
    """
    Import points from LAZ file to LiDAR database

    Uses PDAL to split the input into patches and upload patches to the
    database server. Points from NOAA are pre-classified, so additional
    pre-processing is not needed.

    Beware: no check to avoid duplication, it is up to the user to take care to
        upload data only once
    
    Arguments:
        laz_file: string, path to source file in LAZ format
    
    Returns: Nothing
    """
    logger.info(f'Started ingest: {laz_file}')
    pipeline = pdal.Pipeline(json.dumps({
        "pipeline": [
            {
                "type": "readers.las",
                "filename": laz_file,
            }, {
                "type": "filters.reprojection",
                "out_srs": f"EPSG:{LIDAR_PRJ_SRID}",
            }, {
                "type": "filters.chipper",
                "capacity": 400,
            }, {
                "type": "writers.pgpointcloud",
                "connection": f"host={PSQL_HOST} dbname={LIDAR_DB} user={PSQL_USER} password={PSQL_PASS} port={PSQL_PORT}",
                "table": LIDAR_TABLE,
                "compression": "dimensional",
                "srid": LIDAR_PRJ_SRID,
                "output_dims": "X,Y,Z,ReturnNumber,NumberOfReturns,Classification", # reduce data volume
                "scale_x": 0.01, # precision in meters
                "scale_y": 0.01,
                "scale_z": 0.01, 
                "offset_x": 0, # TODO: select a smarter value
                "offset_y": 0,
                "offset_z": 0,
            }
        ]
    }))
    pipeline.validate() 
    pipeline.execute()
    logger.info(f'Completed ingest: {laz_file}')


def retrieve(xmin, xmax, ymin, ymax, plasio_file=None):
    """
    Retrieve all points within a bounding box
    
    Arguments:
        minx, maxx, miny, maxy: floats, limits for bounding box 
        plasio_file: optional, provide a string to save results as a
            plas.io-friendly LAZ file. If enabled, no array is returned

    Returns: list of numpy arrays per patch, one point per row, named columns
    """
    # build pipeline definition
    pipeline_dict = {
        "pipeline":[
            {
                "type": "readers.pgpointcloud",
                "connection": f"host={PSQL_HOST} dbname={LIDAR_DB} user={PSQL_USER} password={PSQL_PASS} port={PSQL_PORT}",
                "table": LIDAR_TABLE,
                "column": "pa",
            }
          ]
        }
    pipeline_dict['pipeline'][0]['where'] = (
        f"PC_Intersects(pa, ST_MakeEnvelope({xmin}, {xmax}, {ymin}, {ymax}, {LIDAR_PRJ_SRID}))")

    if plasio_file: 
        # optionally write to plasio-friendly LAZ file
        pipeline_dict['pipeline'].extend([
            {
                "type": "writers.las",
                "forward": "all",
                "compression": "laszip",
                "filename": plasio_file,
            }])
    # create and execute pipeline
    pipeline = pdal.Pipeline(json.dumps(pipeline_dict))
    pipeline.validate()
    pipeline.execute()
    # return array, if requested
    if not plasio_file: 
        if not len(pipeline.arrays) == 1:
            raise ValueError('Assumption violated')
        return pipeline.arrays[0]


def grid_points(xmin, xmax, ymin, ymax, grnd=False):
    """
    Grid scattered points using kNN median filter

    Arguments:
        xmin, xmax, ymin, ymax: floats, limits for bounding box 
        grnd: set True to compute surface from ground returns, False to compute
            surface from (first) non-ground returns
    
    Returns: ?
    """
    # constants
    RESOLUTION = 1 # meters

    # build output grid spanning bbox
    x_vec = np.arange(math.ceil(xmin), math.floor(xmax), RESOLUTION)   
    y_vec = np.arange(math.ceil(ymin), math.floor(ymax), RESOLUTION)   
    x_grd, y_grd = np.meshgrid(x_vec, y_vec)

    # retrieve data
    pts = retrieve(xmin, ymin, xmax, ymax)

    # filter for ground returns
    mask = np.zeros(len(pts)) 
    if grnd:
        # extract ground points
        for idx, pt in enumerate(pts):
            if pt[3] == pt[4]  and pt[5] == 2:
                # last or only return, classified as "ground"
                mask[idx] = 1
    else:
        # extract upper surface points
        for idx, pt in enumerate(pts):
            if (pt[3] == 1 or pt[4] == 1) and pt[5] == 1:
                # first or only return, classified as "default"
                mask[idx] = 1
    pts = np.extract(mask, pts)

    # extract [x, y] and z arrays
    npts = len(pts)
    xy = np.zeros((npts, 2))
    zz = np.zeros(npts)
    for idx, pt in enumerate(pts):
        xy[idx, 0] = pt[0]
        xy[idx, 1] = pt[1]
        zz[idx] = pt[2]

    # construct KDTree
    tree = cKDTree(xy) 

    # find NN for all grid points
    xy_grd = np.hstack([x_grd.reshape((-1,1)), y_grd.reshape((-1,1))])
    nn_dist, nn_idx = tree.query(xy_grd, k=10)

    # compute local medians
    # z_grd = np.median(zz[nn_idx], axis=1).reshape(x_grd.shape)
    z_grd = np.mean(zz[nn_idx], axis=1).reshape(x_grd.shape)
    
    # DEBUG: make a quick plot of the results
    plt.imshow(z_grd, cmap='hot', interpolation='nearest')
    plt.show()

    return x_vec, y_vec, z_grd  # TODO: decide what outputs I need



# command line utilities -----------------------------------------------------


def initialize_cli():
    """Command line utility for initializing the LiDAR database"""
    ap = argparse.ArgumentParser(
        description="Initialize Parasol LiDAR database",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter) 
    ap.add_argument('pattern', type=str, help="glob pattern matching files to ingest")
    ap.add_argument('--log', type=str, default='info', help="select logging level",
                    choices=['debug', 'info', 'warning', 'error', 'critical'])
    ap.add_argument('--clean', action='store_true', help='Clobber existing database')
    ap.add_argument('--dryrun', action='store_true', help='Set to preview only')
    args = ap.parse_args()

    log_lvl = getattr(logging, args.log.upper())
    logging.basicConfig(level=log_lvl)
    logger.setLevel(log_lvl)

    input_files = glob(args.pattern)
    
    if args.dryrun:
        print(f'DATABASE: {LIDAR_DB} @ {PSQL_HOST}:{PSQL_PORT}')
        print(f'CLEAN EXISTING: {args.clean}')
        print('FILES:')
        for fn in input_files:
            print(f'\t{fn}')
        return
    
    if args.clean:
        create_db(True)
    for fn in input_files:
        ingest(fn)
        
