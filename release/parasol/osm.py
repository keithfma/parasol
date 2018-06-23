"""
OpenStreetMap data handlers
"""

import os
import pyproj
import logging
import wget
import subprocess

from parasol.common import connect_db, new_db
from parasol import DATA_DIR, GEO_SRID, PRJ_SRID, DOMAIN_XLIM, DOMAIN_YLIM


logger = logging.getLogger(__name__)


# constants
OSM_DIR = os.path.join(DATA_DIR, 'osm')
OSM_FILE = os.path.join(OSM_DIR, 'domain.osm')
    

def create_db(clobber=False):
    """
    Create a new database and initialize for osm dataset

    Arguments:
        clobber: set True to delete and re-initialize an existing database

    Return: Nothing
    """
    # TODO: add index, if necessary
    new_db(OSM_DB, clobber)
    with connect_db() as conn, conn.cursor() as cur:
        cur.execute('CREATE EXTENSION postgis;')
        cur.execute('CREATE EXTENSION pgrouting;')
    logger.info(f'Created new database: {OSM_DB} @ {PSQL_HOST}:{PSQL_PORT}')


def fetch_data():
    """Download OpenStreetMaps data for the Parasol study area"""
    # get OSM bounding box (geographic)
    prj0 = pyproj.Proj(init=f'epsg:{PRJ_SRID}')
    prj1 = pyproj.Proj(init=f'epsg:{GEO_SRID}')
    ll = pyproj.transform(prj0, prj1, DOMAIN_XLIM[0], DOMAIN_YLIM[0])
    lr = pyproj.transform(prj0, prj1, DOMAIN_XLIM[1], DOMAIN_YLIM[0])
    ul = pyproj.transform(prj0, prj1, DOMAIN_XLIM[0], DOMAIN_YLIM[1])
    ur = pyproj.transform(prj0, prj1, DOMAIN_XLIM[1], DOMAIN_YLIM[1])
    lons = [ll[0], lr[0], ur[0], ul[0]]
    lats = [ll[1], lr[1], ur[1], ul[1]]
    
    # create output folder if needed
    if not os.path.isdir(OSM_DIR):
        logger.info(f'Created directory {OSM_DIR}')
        os.makedirs(OSM_DIR)

    # fetch data from OSM overpass API
    # ...cribbed example from: https://github.com/pgRouting/osm2pgrouting/issues/44
    bbox_str = f'{min(lons)},{min(lats)},{max(lons)},{max(lats)}'
    url = f'http://www.overpass-api.de/api/xapi?*[bbox={bbox_str}][@meta]'
    logger.info(f'Downloading OSM data from: {url}')
    wget.download(url, out=OSM_FILE)


def ingest():
    """
    Import points from OSM file to database

    Beware: clobbers existing database contents to avoid duplication
    
    Returns: Nothing
    """
    logger.info(f'Started ingest: {OSM_FILE}')
    subprocess.run(['osm2pgrouting', '-U', PSQL_USER, '-W', PSQL_PASS, '-f',
        OSM_FILE, '-d', OSM_DB,  '--clean'])
    logger.info(f'Completed ingest: {OSM_FILE}')

