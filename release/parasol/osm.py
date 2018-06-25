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
from matplotlib import pyplot as plt

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


def way_points(bbox=None, spacing=cfg.OSM_WAYPT_SPACING):
    """
    Generate evenly-spaced points along all ways in the ROI
    
    NOTE: output is in the projected coord sys defined by cfg.PRJ_SRID 
    
    Arguments
        bbox: 5-element list/tuple, containing bounding box [x_min, x_max,
            y_min, y_max, srid], the srid is an integer spatial reference ID
            (EPSG code) for the float limits. Set None to return all ways in
            the database
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
        where = ''
        if bbox: 
            where = f'WHERE ST_Intersects(ways.the_geom, ST_MakeEnvelope(' \
                    f'{bbox[0]}, {bbox[1]}, {bbox[2]}, {bbox[3]}, {bbox[4]}))'
        geom = f'ST_AsBinary(ST_Transform(the_geom, {cfg.PRJ_SRID}))'  
        cur.execute(f'SELECT gid, {geom} FROM ways {where};')

        # read results and resample each way geometry
        # note: column osm_id is non-unique, do not use this as a key below
        recs = cur.fetchall()
        ways = {}
        for rec in recs:
            # unpack record
            way_id = rec[0]
            line = shapely.wkb.loads(rec[1].tobytes())
            # resample line
            dists = range(0, round(line.length) + 1, spacing)
            line_pts = [line.interpolate(d).xy for d in dists]
            # package results
            way_xy = np.hstack(line_pts).T
            ways[way_id] = way_xy

    return ways 


def plot_way_points(ways, downsample=50):
    """
    Generate simple plot of way points, for debugging
    
    Arguments:
        ways: dict, output from way_points()
        downsample: int, downsampling factor, to ease the load

    Returns: nothing, displays the resulting plot
    """
    display_interval = 500
    for ii, xy in enumerate(ways.values()):
        plt.plot(xy[::downsample, 0], xy[::downsample ,1], '.', color='blue')
        if ii % display_interval == 0:
            print(f'Plotting way {ii+1} of {len(ways)}') 
    plt.show()


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
        
