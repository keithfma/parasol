"""
LiDAR data handlers
"""

import psycopg2 as pg 
import subprocess
import json
import argparse
from glob import glob
import numpy as np
import logging
from pdb import set_trace
import uuid
import os
import json
import subprocess
from pkg_resources import resource_filename
import wget

from parasol import cfg, common


logger = logging.getLogger(__name__)
    

def create_db(clobber=False):
    """
    Create a new database and initialize for lidar point data

    Arguments:
        clobber: set True to delete and re-initialize an existing database

    Return: Nothing
    """
    common.new_db(cfg.LIDAR_DB, clobber)
    with common.connect_db(cfg.LIDAR_DB) as conn, conn.cursor() as cur:
        cur.execute('CREATE EXTENSION postgis;')
        cur.execute('CREATE EXTENSION pointcloud;')
        cur.execute('CREATE EXTENSION pointcloud_postgis;')
        cur.execute(f'CREATE TABLE {cfg.LIDAR_TABLE} (id SERIAL PRIMARY KEY, pa PCPATCH(1));')
        cur.execute(f'CREATE INDEX ON {cfg.LIDAR_TABLE} USING GIST(PC_EnvelopeGeometry(pa));')
    logger.info(f'Created new database: {cfg.LIDAR_DB} @ {cfg.PSQL_HOST}:{cfg.PSQL_PORT}')


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
    pipeline_json = json.dumps({
        "pipeline": [
            {
                "type": "readers.las",
                "filename": laz_file,
            }, {
                "type": "filters.reprojection",
                "out_srs": f"EPSG:{cfg.PRJ_SRID}",
            }, {
                "type": "filters.chipper",
                "capacity": cfg.LIDAR_CHIP,
            }, {
                "type": "writers.pgpointcloud",
                "connection": f"host={cfg.PSQL_HOST} dbname={cfg.LIDAR_DB} user={cfg.PSQL_USER} password={cfg.PSQL_PASS} port={cfg.PSQL_PORT}",
                "table": cfg.LIDAR_TABLE,
                "compression": "dimensional",
                "srid": cfg.PRJ_SRID,
                "output_dims": "X,Y,Z,ReturnNumber,NumberOfReturns,Classification", # reduce data volume
                "scale_x": 0.01, # precision in meters
                "scale_y": 0.01,
                "scale_z": 0.01, 
                "offset_x": 0, # TODO: select a smarter value
                "offset_y": 0,
                "offset_z": 0,
            }
        ]
    })
    subprocess.run(['pdal', 'pipeline', '--stdin'], input=pipeline_json.encode('utf-8'))
    logger.info(f'Completed ingest: {laz_file}')


def retrieve(xmin, xmax, ymin, ymax):
    """
    Retrieve all points within a bounding box
    
    Arguments:
        minx, maxx, miny, maxy: floats, limits for bounding box 

    Returns: numpy array with columns
        X, Y, Z, ReturnNumber, NumberOfReturns, Classification
    """
    # # DISABLED: direct query returns points with reduced precision (AsText) or
    # #   without non-spatial dimensions (AsBinary). Alternative is to write
    # #   custom code to parse the binary directly, which is not currently worth
    # #   the effort
    # with common.connect_db(cfg.LIDAR_DB) as conn, conn.cursor() as cur:
    #     cur.execute(f'SELECT PC_AsText(PC_Union(pa)) FROM lidar WHERE PC_Intersects('
    #         f'pa, ST_MakeEnvelope({xmin}, {ymin}, {xmax}, {ymax}, {cfg.PRJ_SRID}))')
    #     data = np.array(json.loads(cur.fetchone()[0])['pts']) # ordered as ReturnNumber,NumberOfReturns,Classification,X,Y,Z
    # return np.roll(data, 3) # ordered as X,Y,Z,ReturnNumber,NumberOfReturns,Classification

    # build pipeline definition and execute
    filename = uuid.uuid4().hex
    pipeline_json= json.dumps({
        "pipeline":[
            {
                "type": "readers.pgpointcloud",
                "connection": f"host={cfg.PSQL_HOST} dbname={cfg.LIDAR_DB} user={cfg.PSQL_USER} password={cfg.PSQL_PASS} port={cfg.PSQL_PORT}",
                "table": cfg.LIDAR_TABLE,
                "column": "pa",
                # TODO: Holy shit! I think that I had the args wrong all along here! Confirm change.
                # "where": f"PC_Intersects(pa, ST_MakeEnvelope({xmin}, {xmax}, {ymin}, {ymax}, {cfg.PRJ_SRID}))",
                "where": f"PC_Intersects(pa, ST_MakeEnvelope({xmin}, {ymin}, {xmax}, {ymax}, {cfg.PRJ_SRID}))",
            }, {
                "type": "writers.text",
                "format": "csv",
                "filename": filename,
            }
          ]
        })
    subprocess.run(['pdal', 'pipeline', '--stdin'], input=pipeline_json.encode('utf-8'))
    
    # read resulting file to numpy, then delete it
    array = np.loadtxt(filename, delimiter=',', dtype=float, skiprows=1)
    os.remove(filename)
    
    logger.info(f'Received {array.shape[0]} points')
    return array


# command line utilities -----------------------------------------------------


def initialize_cli():
    """Command line utility for initializing the LiDAR database"""
    ap = argparse.ArgumentParser(
        description="Initialize Parasol LiDAR database",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter) 
    ap.add_argument('--urls', type=str, default=resource_filename('parasol', 'lidar_urls.txt'),
        help="path to file containing LiDAR data urls to be downloaded")
    ap.add_argument('--log', type=str, default='info', help="select logging level",
                    choices=['debug', 'info', 'warning', 'error', 'critical'])
    ap.add_argument('--clean', action='store_true', help='Clobber existing database')
    args = ap.parse_args()

    log_lvl = getattr(logging, args.log.upper())
    logging.basicConfig(level=log_lvl)
    logger.setLevel(log_lvl)
    
    # create directory if needed 
    if not os.path.isdir(cfg.LIDAR_DIR):
        os.makedirs(cfg.LIDAR_DIR)

    # get list of urls
    urls = []
    with open(args.urls, 'r') as fp:
        for line in fp:
            line = line.strip()
            if not line:
                continue
            elif line[0] == '#':
                continue
            else:
                urls.append(line)
    
    # download any LiDAR files that are not already there 
    for url in urls:
        filename = os.path.join(cfg.LIDAR_DIR, os.path.basename(url))
        if os.path.isfile(filename):
            logger.info(f'File {filename} exists, skipping')
            continue
        logger.info(f'Downloading URL {url}')
        wget.download(url, out=cfg.LIDAR_DIR) 

    # create db, if requested
    if args.clean:
        create_db(True)
    
    # read data into database
    for fn in glob(os.path.join(cfg.LIDAR_DIR, '*.laz')):
        ingest(fn)

