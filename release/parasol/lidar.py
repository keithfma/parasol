"""
LiDAR data handlers
"""

import psycopg2 as pg 
import subprocess
import json
import pdal

from parasol import LIDAR_DB, LIDAR_TABLE, LIDAR_SRID, PSQL_USER, PSQL_PASS, PSQL_HOST, PSQL_PORT


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
            cur.execute(f'DROP DATABASE IF EXISTS {LIDAR_DB}');
        cur.execute(f'CREATE DATABASE {LIDAR_DB};')
    # init new database
    with connect_db() as conn:
        cur = conn.cursor()
        cur.execute('CREATE EXTENSION postgis;')
        cur.execute('CREATE EXTENSION pointcloud;')
        cur.execute('CREATE EXTENSION pointcloud_postgis;')
        cur.execute(f'CREATE TABLE {LIDAR_TABLE} (id SERIAL PRIMARY KEY, pa PCPATCH(1));')


def ingest(laz_file, clobber=False):
    """
    Import points from LAZ file to LiDAR database

    Uses PDAL to preprocess, split the input into patches, and upload patches to the
    database server. Preprocessing includes outlier detection / removal, ...

    Beware: no check to avoid duplication, it is up to the user to take care to
        upload data only once
    
    Arguments:
        laz_file: string, path to source file in LAZ format
        clobber: set True to delete existing points from this file and re-import
    
    Returns: Nothing
    """
    # TODO: label upper surface points
    # TODO: label ground points
    pipeline = pdal.Pipeline(json.dumps({
        "pipeline": [
            {
                "type": "readers.las",
                "filename": laz_file,
            }, {
                "type": "filters.outlier",
                "method": "statistical",
                "mean_k": 12,
                "multiplier": 2.2,
            }, {
                "type": "filters.chipper",
                "capacity": 400,
            }, {
                "type": "writers.pgpointcloud",
                "connection": f"host={PSQL_HOST} dbname={LIDAR_DB} user={PSQL_USER} password={PSQL_PASS} port={PSQL_PORT}",
                "table": LIDAR_TABLE,
                "compression": "dimensional",
                "srid": LIDAR_SRID,
            }
        ]
    }))
    pipeline.validate() 
    pipeline.execute()

 
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
                "where": f"PC_Intersects(pa, ST_MakeEnvelope({minx}, {maxx}, {miny}, {maxy}, {LIDAR_SRID}))",
            }
          ]
        }
    if plasio_file: 
        # optionally write to plasio-friendly LAZ file
        pipeline_dict['pipeline'].extend([
            {
                "type": "filters.reprojection",
                "out_srs": "EPSG:32619",
            }, {
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


