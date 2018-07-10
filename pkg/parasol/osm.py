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
import pickle
import scipy.interpolate
import scipy.integrate
import numpy as np
import math
import psycopg2
import psycopg2.extras

from parasol import common, cfg, shade


logger = logging.getLogger(__name__)


# constants
OSM_FILE = os.path.join(cfg.OSM_DIR, 'domain.osm')
WAYS_PTS_FILE = os.path.join(cfg.OSM_DIR, 'ways.pkl')
WALKING_SPEED = 1.4 # m/s, see: https://en.wikipedia.org/wiki/Preferred_walking_speed
    

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
        # add extensions
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


# TODO: need to take more care with the end points -- many ways are short and
#   the rouding error matters


def way_points(bbox=None):
    """
    Generate evenly-spaced points along all ways in the ROI
    
    NOTE: output is in the projected coord sys defined by cfg.PRJ_SRID 
    
    Arguments
        bbox: 5-element list/tuple, containing bounding box [x_min, x_max,
            y_min, y_max, srid], the srid is an integer spatial reference ID
            (EPSG code) for the float limits. Set None to return all ways in
            the database

    Returns: 
        ways: dict, keys are way IDs, values are N x 2 numpy arrays containing
            the x, y position of sequential points along the way
        way_pts: dict, keys are way IDs, values are N x 2 numpy arrays
            containing the x, y position of evenly-spaced sequential points
            interpolated along the way.  The first row is always the start
            point, and the last is always the endpoint. Spacing for the last
            point for each way is generally less than the desired spacing,
            beware! this will cause an overshoot of up to spacing for the last
            point
    """
    logger.info(f'Computing way points, bbox={bbox}, spacing={cfg.OSM_WAYPT_SPACING}')
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
        way_pts = {}
        ways = {}
        for rec in recs:
            # unpack record
            way_id = rec[0]
            line = shapely.wkb.loads(rec[1].tobytes())
            ways[way_id] = np.vstack(line.xy).T
            # resample line
            dists = range(0, round(line.length) + 1, cfg.OSM_WAYPT_SPACING) 
            line_pts = [line.interpolate(d).xy for d in dists]
            way_pts[way_id] = np.hstack(line_pts).T
    logger.info(f'Completed way points for {len(ways)} ways')

    return way_pts 


def way_insolation(hour, minute, wpts):
    """
    Compute path-integrated insolation for all ways

    Arguments:
        hour, minute: time to compute insolation, will use nearest if not an
            exact match
        wpts: dict, output from way_points(), contains way gid as keys, and
            evenly spaced points along way as values
    
    Returns: jm2_sun, jm2_shade
        jm2_sun: dict, contains way gid as key, integrated sun power as
            values (units are J/m2, assuming a constant walking speed)
        jm2_shade: dict, contains way gid as key, integrated loss in sun power
            due to shade as values (units are J/m2, assuming a constant walking
            speed)
    """
    # retrieve shade raster for nearest available time
    xx, yy, wm2 = shade.retrieve(hour, minute, kind='bottom')
    yy = yy[::-1] # interpolant requires increasing coords
    wm2 = wm2[:, ::-1]

    # normalize insolation grid
    wm2 = wm2 - np.nanmin(wm2)
    wm2 = wm2/np.nanmax(wm2)
    wm2[np.isnan(wm2)] = 0.5

    # interpolate values at all way points
    # note: wm2_sun + wm2_shade = constant = wm2_max - wm2_min
    interp = scipy.interpolate.RectBivariateSpline(xx, yy, wm2, kx=1, ky=1)
    wm2_sun = {}
    wm2_shade = {}
    for gid, xy in wpts.items():
        wm2_pts = interp(xy[:,0], xy[:,1], grid=False)
        wm2_sun[gid] = wm2_pts # W/m2 due to sun
        wm2_shade[gid] = 1 - wm2_pts # lost W/m2 due to shade
    
    # integrate sun/shade watts/m2 along path for each segment -> J/m2
    # note: integration incorporates length into both costs
    jm2_sun = {}
    for gid, pts in wm2_sun.items():
        jm2_sun[gid] = scipy.integrate.trapz(pts, dx=cfg.OSM_WAYPT_SPACING)
    jm2_shade = {}
    for gid, pts in wm2_shade.items():
        jm2_shade[gid] = scipy.integrate.trapz(pts, dx=cfg.OSM_WAYPT_SPACING)
    
    return jm2_sun, jm2_shade


def update_cost_db(wpts):
    """
    Update insolation cost columns for all way elements in OSM database

    Arguments:
        wpts: dict, output from way_points(), contains way gid as keys, and
            evenly spaced points along way as values
    
    Returns: Nothing, sets values in cost_insolation_HHMM columns of OSM DB
    """
    with common.connect_db(cfg.OSM_DB) as conn:
        
        # loop over all calculated times 
        for meta in common.shade_meta():
            with conn.cursor() as cur:
            
                # compute the cost at this time
                logger.info(f'Updating insolation cost for {meta["hour"]:02d}:{meta["minute"]:02d}')
                sun_cost, shade_cost = way_insolation(meta["hour"], meta["minute"], wpts)

                # prepare columns
                cur.execute(f'ALTER TABLE ways ADD COLUMN IF NOT EXISTS {meta["sun_cost"]} float8;')
                cur.execute(f'ALTER TABLE ways ADD COLUMN IF NOT EXISTS {meta["shade_cost"]} float8;')

                # run batch of sql updates
                sql = f'UPDATE ways SET {meta["sun_cost"]} = %(cost)s WHERE gid = %(gid)s' 
                params = [{'gid': x[0], 'cost': x[1]} for x in sun_cost.items()]
                psycopg2.extras.execute_batch(cur, sql, params, page_size=1000)
                
                sql = f'UPDATE ways SET {meta["shade_cost"]} = %(cost)s WHERE gid = %(gid)s' 
                params = [{'gid': x[0], 'cost': x[1]} for x in shade_cost.items()]
                psycopg2.extras.execute_batch(cur, sql, params, page_size=1000)


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

    # init waypoint lookup table
    # TODO: move this into the database - one less file to worry about
    wpts = way_points() # compute all
    with open(WAYS_PTS_FILE, 'wb') as fp:
        pickle.dump(wpts, fp)


def update_cli():
    """Command line utiltiy for updating solar cost values in OSM DB"""
    ap = argparse.ArgumentParser(
        description="Update insolation cost in Parasol OSM database",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter) 
    ap.add_argument('--log', type=str, default='info', help="select logging level",
                    choices=['debug', 'info', 'warning', 'error', 'critical'])
    args = ap.parse_args()

    log_lvl = getattr(logging, args.log.upper())
    logging.basicConfig(level=log_lvl)
    logger.setLevel(log_lvl)
    
    with open(WAYS_PTS_FILE, 'rb') as fp:
        wpts = pickle.load(fp)
    update_cost_db(wpts)

