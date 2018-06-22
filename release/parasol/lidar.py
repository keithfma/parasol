"""
LiDAR data handlers
"""

import psycopg2 as pg 
import subprocess
import json
import pdal
import argparse
from glob import glob
import numpy as np
import logging
from pdb import set_trace
import uuid
import os
import json

from parasol import LIDAR_DB, LIDAR_TABLE, GEO_SRID, PRJ_SRID, \
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
                "out_srs": f"EPSG:{PRJ_SRID}",
            }, {
                "type": "filters.chipper",
                "capacity": 400,
            }, {
                "type": "writers.pgpointcloud",
                "connection": f"host={PSQL_HOST} dbname={LIDAR_DB} user={PSQL_USER} password={PSQL_PASS} port={PSQL_PORT}",
                "table": LIDAR_TABLE,
                "compression": "dimensional",
                "srid": PRJ_SRID,
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


def retrieve_db(xmin, xmax, ymin, ymax):
    """
    Retrieve all points within a bounding box

    NOTE: intersection is at the patch level - meaning the output set will
        likely contain points outside the specified ROI. This is OK for my
        purposes, so I do not bother culling the resulting point set.
    
    Arguments:
        minx, maxx, miny, maxy: floats, limits for bounding box 

    Returns: numpy array with columns
        X, Y, Z, ReturnNumber, NumberOfReturns, Classification
    """
    with connect_db() as conn, conn.cursor() as cur:
        sql = f"SELECT PC_AsText(pa) FROM lidar WHERE PC_Intersects(lidar.pa, ST_MakeEnvelope({xmin}, {ymin}, {xmax}, {ymax}, {PRJ_SRID}))"
        cur.execute(sql)
        recs = cur.fetchall()
    pts = []
    for rec in recs:
        patch = json.loads(rec[0])
        pts.extend(patch['pts'])

    return np.array(pts)


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
        
