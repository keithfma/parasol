"""
LiDAR data handlers
"""

import psycopg2 as pg 
import subprocess
import json
import pdal

from parasol import LIDAR_DB, PSQL_USER, PSQL_PASS, PSQL_HOST, PSQL_PORT


def connect_db():
    """Connect to lidar DB and return cursor"""
    conn = pg.connect(dbname=LIDAR_DB, user=PSQL_USER, password=PSQL_PASS,
        host=PSQL_HOST, port=PSQL_PORT)
    return conn.cursor()
    

def create_db(clobber=False):
    """
    Create a new database and initialize for lidar point data

    Arguments:
        clobber: set True to delete and re-initialize an existing database

    Return: cursor to database
    """
    # connect to default database
    conn = pg.connect(dbname='postgres', user=PSQL_USER, password=PSQL_PASS,
        host=PSQL_HOST, port=PSQL_PORT)
    conn.set_isolation_level(pg.extensions.ISOLATION_LEVEL_AUTOCOMMIT) 
    cur = conn.cursor()
    # clobber existing, if requested
    if clobber:
        cur.execute(f'DROP DATABASE IF EXISTS {LIDAR_DB}');
    # create new database with required extensions
    cur.execute(f'CREATE DATABASE {LIDAR_DB};')
    # connect to new database
    con = connect_db()
    con.execute('CREATE EXTENSION postgis;')
    con.execute('CREATE EXTENSION pointcloud;')
    # done 
    return cur 


def ingest_laz(laz_file, clobber=False):
    """
    Import points from LAZ file to LiDAR database

    Uses PDAL to split the input into patches and upload patches to the
    database server. Checks metadata to avoid duplication
    
    Arguments:
        laz_file: string, path to source file in LAZ format
        clobber: set True to delete existing points from this file and re-import
    
    Returns: ?
    """
    pipeline = pdal.Pipeline(json.dumps({
        "pipeline": [
            {
                "type": "readers.las",
                "filename": laz_file,
            }, {
                "type": "writers.las",
                "filename": "delete_me.laz",
                "forward": "all",
                "compression": "laszip",
            }
        ]
    }))
    pipeline.validate() 
    pipeline.execute()

    return pipeline # DEBUG
    
    

# TODO: label upper surface points
# TODO: label ground points


