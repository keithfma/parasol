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
import matplotlib
import pickle
import scipy.interpolate
import scipy.integrate

from parasol import common, cfg, shade


logger = logging.getLogger(__name__)


# constants
OSM_FILE = os.path.join(cfg.OSM_DIR, 'domain.osm')
WAYS_FILE = os.path.join(cfg.OSM_DIR, 'ways_pts.pkl')
WAYS_PTS_FILE = os.path.join(cfg.OSM_DIR, 'ways.pkl')
    

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

    return ways, way_pts 


def way_insolation(hour, minute, wpts):
    """
    Compute path-integrated insolation for all ways

    Arguments:
        hour, minute: time to compute insolation, will use nearest if not an
            exact match
        wpts: dict, output from way_points(), contains way gid as keys, and
            evenly spaced points along way as values
    
    Returns: spts, stot
        spts: dict, contains way gid as key, point observations of insolation
            as values (units are W/m2)
        stot: dict, contains way gid as key, integrated insolation as
            values (units are J/m2, assuming a constant walking speed)
    """
    # retrieve shade raster for nearest available time
    xx, yy, zz = shade.retrieve(hour, minute)
    yy = yy[::-1] # interpolant requires increasing coords
    zz = zz[:, ::-1]
    np.nan_to_num(zz, copy=False)              

    # interpolate values at all way points
    interp = scipy.interpolate.RectBivariateSpline(xx, yy, zz, kx=1, ky=1)
    spts = {}
    for gid, xy in wpts.items():
        spts[gid] = interp(xy[:,0], xy[:,1], grid=False)

    # integrate along path for each segment
    # TODO: convert units by dividing out a (constant) walking speed
    stot = {}
    for gid, ss in spts.items():
        stot[gid] = scipy.integrate.trapz(ss, dx=cfg.OSM_WAYPT_SPACING)
    
    return spts, stot


def plot_way_insolation_pts(pts, pts_sol, vmin=100, vmax=1000, downsample=1, show=True):
    """
    Generate simple plot of way points
    
    Arguments:
        pts: dict, output from way_points()
        downsample: int, downsampling factor, to ease the load
        show: set True to display plot, else, do nothing to give the user a
            chance to make modifications first

    Returns: nothing, displays the resulting plot
    """
    xx = []; yy = []; zz = []
    for gid in pts.keys():
        xx.extend(pts[gid][::downsample, 0])
        yy.extend(pts[gid][::downsample, 1])
        zz.extend(pts_sol[gid][::downsample])
    plt.scatter(xx, yy, c=zz, cmap='viridis', vmin=vmin, vmax=vmax, marker='.')
    if show:
        plt.show()


def plot_way_insolation(ways, ways_sol, vmin=1000, vmax=10000, downsample=5, show=True):
    """
    Generate simple plot of way integrated insolation
    
    Arguments:
        ways: dict, output from way_pts 
        way_sol: dict, output from way_insolation()
        vmin, vmax: color scale limits
        downsample: int, downsampling factor, to ease the load
        show: set True to display plot, else, do nothing to give the user a
            chance to make modifications first

    Returns: nothing, displays the resulting plot
    """
    # setup color scale
    cm = matplotlib.cm.ScalarMappable(
        norm=matplotlib.colors.Normalize(vmin=vmin, vmax=vmax),
        cmap='viridis')

    # build lists of lines and colors
    lines = [], colors = []
    for gid in gids:
        this_way = ways[gid]
        this_way_sol = ways_sol[gid]
        this_line = []
        for ii in range(this_way.shape[0]):
            this_line.append((this_way[ii,0], this_way[ii,1]))
        this_color = cm.to_rgba(this_way_sol)

    # plot at-once using line collection approach


    if show:
        plt.show()


def update_cost_columns(wpts):
    """
    Update insolation cost columns for all way elements in OSM database

    Arguments:
        wpts: dict, output from way_points(), contains way gid as keys, and
            evenly spaced points along way as values
    
    Returns: Nothing, sets values in cost_insolation_HHMM columns of OSM DB
    """
    return NotImplementedError


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

    # init database    
    create_db(True)
    fetch_data()
    ingest()

    # init waypoint lookup table
    ways, pts = way_points() # compute all
    with open(WAYS_FILE, 'wb') as fp:
        pickle.dump(ways, fp)
    with open(WAYS_PTS_FILE, 'wb') as fp:
        pickle.dump(pts, fp)


def update_cli():
    """Command line utiltiy for updating solar cost values in OSM DB"""
    raise NotImplementedError 


