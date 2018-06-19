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
from parasol import LIDAR_DB, LIDAR_TABLE, LIDAR_GEO_SRID, LIDAR_PRJ_SRID, \
    PSQL_USER, PSQL_PASS, PSQL_HOST, PSQL_PORT


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
            }
        ]
    }))
    pipeline.validate() 
    pipeline.execute()
    logger.info(f'Completed ingest: {laz_file}')

 
def retrieve(minx, maxx, miny, maxy, plasio_file=None):
    """
    Retrieve all points within a bounding box
    
    Arguments:
        minx, maxx: floats, x-limits for bounding box 
        miny, maxy: floats, y-limits for bounding box 
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
                "where": f"PC_Intersects(pa, ST_MakeEnvelope({minx}, {maxx}, {miny}, {maxy}, {LIDAR_PRJ_SRID}))",
            }
          ]
        }
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
        return pipeline.arrays


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
        
