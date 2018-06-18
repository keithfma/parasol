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

    Uses PDAL to split the input into patches and upload patches to the
    database server. Checks metadata to avoid duplication
    
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
   
 
def retrieve(minx, maxx, miny, maxy):
    """
    Retrieve all points within a bounding box
    
    Arguments:
        minx, maxx: floats, x-limits for bounding box 
        miny, maxy: floats, y-limits for bounding box 

    Returns: list of numpy arrays (per patch), one point per row with named columns
    """
    pipeline = pdal.Pipeline(json.dumps({
        "pipeline":[
            {
                "type": "readers.pgpointcloud",
                "connection": f"host={PSQL_HOST} dbname={LIDAR_DB} user={PSQL_USER} password={PSQL_PASS} port={PSQL_PORT}",
                "table": LIDAR_TABLE,
                "column": "pa",
                "where": f"PC_Intersects(pa, ST_MakeEnvelope({minx}, {maxx}, {miny}, {maxy}, {LIDAR_SRID}))",
            }
          ]
        }))
    pipeline.validate()
    pipeline.execute()
    return pipeline.arrays



