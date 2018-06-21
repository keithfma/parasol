"""
Raster data handlers
"""

import logging
import psycopg2 as pg
import numpy as np
import math
from scipy.spatial import cKDTree
import gdal
import osr
import subprocess
from pdb import set_trace
import tempfile
import matplotlib
from matplotlib import pyplot as plt
import argparse
import gc

from parasol import lidar
from parasol.common import tile_limits
from parasol import RASTER_DB, PSQL_USER, PSQL_PASS, PSQL_HOST, PSQL_PORT, \
    PRJ_SRID, SURFACE_TABLE, GROUND_TABLE, DOMAIN_XLIM, DOMAIN_YLIM

logger = logging.getLogger(__name__)


# constants
RESOLUTION = 1 # meters
PAD = 10 # meters
TILE_DIM = 1000 # meters


def connect_db(dbname=RASTER_DB):
    """
    Return connection to raster DB and return cursor

    Arguments:
        dbname: string, database name to connect to

    Returns: psycopg2 connection object
    """
    conn = pg.connect(dbname=dbname, user=PSQL_USER, password=PSQL_PASS,
        host=PSQL_HOST, port=PSQL_PORT)
    return conn
    

def create_db(clobber=False):
    """
    Create a new database and initialize for gridded raster data

    Arguments:
        clobber: set True to delete and re-initialize an existing database

    Return: Nothing
    """
    # TODO: add indexes as needed
    # connect to default database
    with connect_db('postgres') as conn, conn.cursor() as cur:
        conn.set_isolation_level(pg.extensions.ISOLATION_LEVEL_AUTOCOMMIT) 
        if clobber:
            logger.info(f'Dropped existing database: {RASTER_DB} @ {PSQL_HOST}:{PSQL_PORT}')
            cur.execute(f'DROP DATABASE IF EXISTS {RASTER_DB}');
        cur.execute(f'CREATE DATABASE {RASTER_DB};')
        cur.close()
    # init new database
    with connect_db() as conn, conn.cursor() as cur:
        cur.execute('CREATE EXTENSION postgis;')
    logger.info(f'Created new database: {RASTER_DB} @ {PSQL_HOST}:{PSQL_PORT}')


def grid_points(x_min, x_max, y_min, y_max, grnd=False):
    """
    Grid scattered points using kNN median filter

    Arguments:
        x_min, x_max, y_min, y_max: floats, limits for bounding box 
        grnd: set True to compute surface from ground returns, False to compute
            surface from (first) non-ground returns
    
    Returns: x_vec, y_vec, z_grd
        x_vec, y_vec: numpy 1D arrays, x and y coordinate axes
        z_grd: numpy 2D array, elevation grid 
    """

    # # build output grid spanning bbox
    # x_vec = np.arange(math.floor(x_min), math.floor(x_max), RESOLUTION)   
    # y_vec = np.arange(math.floor(y_min), math.floor(y_max), RESOLUTION)   
    # x_grd, y_grd = np.meshgrid(x_vec, y_vec)

    # retrieve data, including a pad on all sides
    # pts = lidar.retrieve(x_min-PAD, y_min-PAD, x_max+PAD, y_max+PAD)
    lidar.retrieve(x_min-PAD, y_min-PAD, x_max+PAD, y_max+PAD, 'delete_me.laz')

    # # filter for ground returns
    # mask = np.zeros(len(pts)) 
    # if grnd:
    #     # extract ground points
    #     for idx, pt in enumerate(pts):
    #         if pt[3] == pt[4]  and pt[5] == 2:
    #             # last or only return, classified as "ground"
    #             mask[idx] = 1
    # else:
    #     # extract upper surface points
    #     for idx, pt in enumerate(pts):
    #         if (pt[3] == 1 or pt[4] == 1) and pt[5] == 1:
    #             # first or only return, classified as "default"
    #             mask[idx] = 1
    # pts = np.extract(mask, pts)

    # # extract [x, y] and z arrays
    # npts = len(pts)
    # xy = np.zeros((npts, 2))
    # zz = np.zeros(npts)
    # for idx, pt in enumerate(pts):
    #     xy[idx, 0] = pt[0]
    #     xy[idx, 1] = pt[1]
    #     zz[idx] = pt[2]

    # # construct KDTree
    # tree = cKDTree(xy) 

    # # find NN for all grid points
    # xy_grd = np.hstack([x_grd.reshape((-1,1)), y_grd.reshape((-1,1))])
    # nn_dist, nn_idx = tree.query(xy_grd, k=16)

    # # compute local medians
    # z_grd = np.median(zz[nn_idx], axis=1).reshape(x_grd.shape)

    # return x_vec, y_vec, z_grd


def create_geotiff(filename, x_vec, y_vec, z_grd):
    """
    Write input array as GeoTiff raster
    
    Arguments:
        filename: string, path to write GeoTiff file
        x_vec, y_vec: numpy 1D arrays, x and y coordinate axes
        z_grd: numpy 2D array, elevation grid 

    Returns: Nothing, writes result to file
    """
    # invert y-axis
    y_vec = y_vec[::-1]
    z_grd = z_grd[::-1,:]
    # create file
    rows, cols = z_grd.shape
    driver = gdal.GetDriverByName('GTiff')
    outRaster = driver.Create(filename, cols, rows, 1, gdal.GDT_Float32)
    outRaster.SetGeoTransform((x_vec[0], RESOLUTION, 0, y_vec[0], 0, -RESOLUTION))
    outband = outRaster.GetRasterBand(1)
    outband.WriteArray(z_grd)
    outRasterSRS = osr.SpatialReference()
    outRasterSRS.ImportFromEPSG(PRJ_SRID)
    outRaster.SetProjection(outRasterSRS.ExportToWkt())
    outband.FlushCache()
    # clean up
    driver = outRaster = outband = None


def upload_geotiff(filename, tablename, mode):
    """
    Upload GeoTiff file to database

    Command-line tool 'rastertopsql' used to generate SQL commands

    Arguments:
        filename: string, GeoTiff file to upload
        tablename: string, target table in DB
        mode: string, one of 'create', 'add', 'finish'. create mode initializes
            the raster table and appends the raster, add mode appends the
            raster, and finish mode appends the raster and sets the constraints.
    
    Returns: Nothing
    """
    # generate sql commands
    if mode == 'create':
        cmd = f'raster2pgsql -d -s {PRJ_SRID} -b 1 -t auto {filename} {tablename}'
    elif mode == 'add' or mode == 'finish':
        cmd = f'raster2pgsql -a -s {PRJ_SRID} -b 1 {filename} {tablename}'
    else:
        raise ValueError('mode argument not recognized')
    out = subprocess.run(cmd.split(' '), stdout=subprocess.PIPE, check=True)
    sql = out.stdout.decode('utf-8')
    if mode == 'finish':
        sql += (f"SELECT AddRasterConstraints('','{tablename}','rast',"
                "TRUE,TRUE,TRUE,TRUE,TRUE,TRUE,TRUE,TRUE,TRUE,TRUE,TRUE,TRUE);")
    
    # execute sql commands
    with connect_db() as conn, conn.cursor() as cur:
        cur.execute(sql)
        cur.close()


def new_surface(x_min, x_max, y_min, y_max, x_tile, y_tile):
    """
    Generate rasters and upload to database, tile-by-tile

    Arguments:
        x_min, x_max, y_min, y_max: floats, limits for the full region-of-interest
        x_tile, y_tile: floats, desired dimensions for generated tiles, note that
            the actual dimensions are adjusted to evenly divide the ROI
    
    Returns: nothing
    """
    tiles = tile_limits(x_min, x_max, y_min, y_max, x_tile, y_tile)
    num_tiles = len(tiles)

    modes = ['add'] * len(tiles)
    modes[0] = 'create'
    modes[-1] = 'finish'

    for ii, tile in enumerate(tiles):
        logger.info(f'Generating tile {ii+1} of {num_tiles} - surface')
        grid_points(**tile)
        # x_vec, y_vec, z_grd = grid_points(**tile)
        with tempfile.NamedTemporaryFile() as fp:
            # create_geotiff(fp.name, x_vec, y_vec, z_grd)
            # upload_geotiff(fp.name, SURFACE_TABLE, modes[ii])
            fp.close()
        logger.info(f'Generating tile {ii+1} of {num_tiles} - ground')
        grid_points(**tile, grnd=True)
        # x_vec, y_vec, z_grd = grid_points(**tile, grnd=True)
        with tempfile.NamedTemporaryFile() as fp:
            # create_geotiff(fp.name, x_vec, y_vec, z_grd)
            # upload_geotiff(fp.name, GROUND_TABLE, modes[ii])
            fp.close()
            # gc.collect(2)


def _as_numpy(data):
    """Convert binary raster data from DB to numpy array"""
    # read data to GDAL object
    # See: https://gis.stackexchange.com/questions/130139/downloading-raster-data-into-python-from-postgis-using-psycopg2 
    vsipath = '/vsimem/parasol' # must be in this root path
    gdal.FileFromMemBuffer(vsipath, bytes(data))
    ds = gdal.Open(vsipath)
    band = ds.GetRasterBand(1)
    arr = band.ReadAsArray()
    # TODO: get coordinate vectors, use ds.GetGeoTransform, and go from there
    ds = band = None
    gdal.Unlink(vsipath)
    # replace NODATA with np.nan
    dtype_max = np.finfo(arr.dtype).max
    dtype_min = np.finfo(arr.dtype).min
    arr[arr == dtype_max] = np.nan
    arr[arr == dtype_min] = np.nan
    # done!
    return arr


def _as_geotiff(data, filename):
    """Convert binary raster data from DB to geotiff file"""
    with open(filename, 'wb') as fp:
        fp.write(bytes(data))


def retrieve(x_min, x_max, y_min, y_max, kind, filename=None, plot=False):
    """
    Retrieve subset of raster from database

    Arguments:
        x_min, x_max, y_min, y_max: floats, limits for the region to retrieve
        kind: string, one of 'surface', 'ground', selects raster to retrieve
        filename: string or None, provide a filename to save to geotiff
        plot: set True to make a quick plot for debugging, only valid if
            filename is not set
    
    Returns: numpy array (if filename == None) or None
    """
    # parse input arguments
    if kind == 'surface':
        table_name = SURFACE_TABLE
    elif kind == 'ground':
        table_name = GROUND_TABLE
    else:
        raise ValueError('Invalid selection for argument "kind"')
    if filename and plot:
        raise ValueError("Can't plot if 'filename' is provided")
    
    # get raster data from DB
    sql = f"""
    SELECT
        ST_AsGDALRaster(
            ST_Union(ST_Clip(rast, ST_MakeEnvelope({x_min}, {y_min}, {x_max}, {y_max}, {PRJ_SRID}))),
                'GTiff'
        )
        FROM {table_name};
    """
    with connect_db() as conn, conn.cursor() as cur:
        cur.execute(sql)
        data = cur.fetchone()[0]
        cur.close()

    if filename:
        # handle writing to geotiff
        _as_geotiff(data, filename)
        arr = None

    else:
        # handle reading to numpy array
        arr = _as_numpy(arr)
        if plot: 
            current_cmap = matplotlib.cm.get_cmap()
            current_cmap.set_bad(color='red')   
            plt.imshow(arr)
            plt.show()
     
    # done!
    return arr


# command line utilities -----------------------------------------------------


def initialize_cli():
    """Command line utility for initializing the surface/ground databases"""
    ap = argparse.ArgumentParser(
        description="Initialize Parasol surface & ground raster databases - clobbers existing!",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter) 
    ap.add_argument('--log', type=str, default='info', help="select logging level",
                    choices=['debug', 'info', 'warning', 'error', 'critical'])
    ap.add_argument('--dryrun', action='store_true', help='Set to preview only')
    args = ap.parse_args()

    log_lvl = getattr(logging, args.log.upper())
    logging.basicConfig(level=log_lvl)
    logger.setLevel(log_lvl)

    if (args.dryrun):
        tiles = tile_limits(DOMAIN_XLIM[0], DOMAIN_XLIM[1], DOMAIN_YLIM[0],
            DOMAIN_YLIM[1], TILE_DIM, TILE_DIM)
        print(f'Compute raster in domain: [[{DOMAIN_XLIM}], [{DOMAIN_YLIM}]]')
        print(f'Num tiles: {len(tiles)}')
    
    else:
        create_db(True)
        new_surface(DOMAIN_XLIM[0], DOMAIN_XLIM[1], DOMAIN_YLIM[0],
            DOMAIN_YLIM[1], TILE_DIM, TILE_DIM)
