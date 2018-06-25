"""
OpenStreetMap data handlers
"""

import os
import pyproj
import logging
import wget
import subprocess
import argparse
from pdb import set_trace
import shapely.wkb
import numpy as np

from parasol import common, cfg


logger = logging.getLogger(__name__)


# constants
OSM_FILE = os.path.join(cfg.OSM_DIR, 'domain.osm')
    

def create_db(clobber=False):
    """
    Create a new database and initialize for osm dataset

    Arguments:
        clobber: set True to delete and re-initialize an existing database

    Return: Nothing
    """
    # TODO: add index, if necessary
    common.new_db(cfg.OSM_DB, clobber)
    with common.connect_db(cfg.OSM_DB) as conn, conn.cursor() as cur:
        cur.execute('CREATE EXTENSION postgis;')
        cur.execute('CREATE EXTENSION pgrouting;')


def fetch_data():
    """Download OpenStreetMaps data for the Parasol study area"""
    # get OSM bounding box (geographic)
    prj0 = pyproj.Proj(init=f'epsg:{cfg.PRJ_SRID}')
    prj1 = pyproj.Proj(init=f'epsg:{cfg.GEO_SRID}')
    ll = pyproj.transform(prj0, prj1, cfg.DOMAIN_XLIM[0], cfg.DOMAIN_YLIM[0])
    lr = pyproj.transform(prj0, prj1, cfg.DOMAIN_XLIM[1], cfg.DOMAIN_YLIM[0])
    ul = pyproj.transform(prj0, prj1, cfg.DOMAIN_XLIM[0], cfg.DOMAIN_YLIM[1])
    ur = pyproj.transform(prj0, prj1, cfg.DOMAIN_XLIM[1], cfg.DOMAIN_YLIM[1])
    lons = [ll[0], lr[0], ur[0], ul[0]]
    lats = [ll[1], lr[1], ur[1], ul[1]]
    
    # create output folder if needed
    if not os.path.isdir(cfg.OSM_DIR):
        logger.info(f'Created directory {cfg.OSM_DIR}')
        os.makedirs(cfg.OSM_DIR)

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
    subprocess.run(['osm2pgrouting', '-U', cfg.PSQL_USER, '-W', cfg.PSQL_PASS, '-f',
        OSM_FILE, '-d', cfg.OSM_DB,  '--clean'])
    logger.info(f'Completed ingest: {OSM_FILE}')


def way_points(x_min, x_max, y_min, y_max, srid, spacing):
    """
    Generate evenly-spaced points along all ways in the ROI
    
    NOTE: 
    
    Arguments
        x_min, x_max, y_min, y_max: floats, bounding box for ROI
        srid: int, spatial reference ID (EPSG code) for the bounding box
        spacing: float, space between adjacent points along each way

    Returns: 
        ways: dict, keys are way IDs, values are N x 2 numpy arrays
            containing the x, y position of sequential points along the way.
            The first row is always the start point, and the last is always the
            endpoint. Spacing for the last point for each way is generally less
            than the desired spacing, beware!
    """
    with common.connect_db(cfg.OSM_DB) as conn, conn.cursor() as cur:
        
        # query returning geometry of all ways
        # note: column osm_id is non-unique, do not use this as a key below
        envelope = f'ST_MakeEnvelope({x_min}, {y_min}, {x_max}, {y_max}, {srid})'
        cur.execute(f'SELECT gid, ST_AsBinary(the_geom) FROM ways WHERE ST_Intersects(ways.the_geom, {envelope});')

        # read results and resample each way geometry
        recs = cur.fetchall()
        ways = {}
        for rec in recs:
            way_id = rec[0]
            line = shapely.wkb.loads(rec[1].tobytes())
            # TODO: resample!
            way_xy = np.vstack(line.xy).T
            ways[way_id] = way_xy

    # return ways
    return recs


# command line utilities -----------------------------------------------------


def initialize_cli():
    """Command line utility for initializing the OSM database"""
    ap = argparse.ArgumentParser(
        description="Initialize Parasol OSM database",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter) 
    ap.add_argument('--log', type=str, default='info', help="select logging level",
                    choices=['debug', 'info', 'warning', 'error', 'critical'])
    args = ap.parse_args()

    log_lvl = getattr(logging, args.log.upper())
    logging.basicConfig(level=log_lvl)
    logger.setLevel(log_lvl)

    create_db(True)
    fetch_data()
    ingest()
        
