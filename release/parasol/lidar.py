"""
LiDAR data handlers
"""

import psycopg2 as pg 
import subprocess
import json

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


# def lidar_fetch():
#     """
#     Download LiDAR tiles for the Parasol study area
#     """
#     # get tile urls
#     with open(LIDAR_URLS_FILE, 'r') as fp:
#         lidar_urls = json.load(fp)
# 
#     # create output folder if needed
#     if not os.path.isdir(PARASOL_LIDAR_RAW):
#         logger.info(f'Created directory {PARASOL_LIDAR_RAW}')
#         os.makedirs(PARASOL_LIDAR_RAW)
#    
#     # download all tiles, skip if they exist 
#     for url in lidar_urls:
#         file_name = os.path.join(PARASOL_LIDAR_RAW, os.path.basename(url))
#         if os.path.isfile(file_name):
#             logging.info(f'LiDAR file {file_name} exists, skipping download')
#         else:
#             logging.info(f'Downloading LiDAR file {url}')
#             wget.download(url, out=file_name)
