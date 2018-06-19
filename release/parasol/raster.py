"""
Raster data handlers
"""

import logging
import psycopg2 as pg
import numpy as np
import math
from scipy.spatial import cKDTree
from osgeo import gdal, osr
import subprocess


from parasol import lidar
from parasol import RASTER_DB, PSQL_USER, PSQL_PASS, PSQL_HOST, PSQL_PORT, PRJ_SRID
# TODO: need separate DB for top, bottom, shade rasters
# TODO: should I project or just stay in geographic coords?


logger = logging.getLogger(__name__)


# constants
RESOLUTION = 1 # meters


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
    with connect_db('postgres') as conn:
        conn.set_isolation_level(pg.extensions.ISOLATION_LEVEL_AUTOCOMMIT) 
        cur = conn.cursor()
        if clobber:
            logger.info(f'Dropped existing database: {RASTER_DB} @ {PSQL_HOST}:{PSQL_PORT}')
            cur.execute(f'DROP DATABASE IF EXISTS {RASTER_DB}');
        cur.execute(f'CREATE DATABASE {RASTER_DB};')
    # init new database
    with connect_db() as conn:
        cur = conn.cursor()
        cur.execute('CREATE EXTENSION postgis;')
        # TODO: create relevant tables, if needed
    logger.info(f'Created new database: {RASTER_DB} @ {PSQL_HOST}:{PSQL_PORT}')


# TODO: add a "pad_width" to allow for better edge treatment
def grid_points(xmin, xmax, ymin, ymax, grnd=False):
    """
    Grid scattered points using kNN median filter

    Arguments:
        xmin, xmax, ymin, ymax: floats, limits for bounding box 
        grnd: set True to compute surface from ground returns, False to compute
            surface from (first) non-ground returns
    
    Returns: x_vec, y_vec, z_grd
        x_vec, y_vec: numpy 1D arrays, x and y coordinate axes
        z_grd: numpy 2D array, elevation grid 
    """

    # build output grid spanning bbox
    x_vec = np.arange(math.ceil(xmin), math.floor(xmax), RESOLUTION)   
    y_vec = np.arange(math.ceil(ymin), math.floor(ymax), RESOLUTION)   
    x_grd, y_grd = np.meshgrid(x_vec, y_vec)

    # retrieve data
    pts = lidar.retrieve(xmin, ymin, xmax, ymax)

    # filter for ground returns
    mask = np.zeros(len(pts)) 
    if grnd:
        # extract ground points
        for idx, pt in enumerate(pts):
            if pt[3] == pt[4]  and pt[5] == 2:
                # last or only return, classified as "ground"
                mask[idx] = 1
    else:
        # extract upper surface points
        for idx, pt in enumerate(pts):
            if (pt[3] == 1 or pt[4] == 1) and pt[5] == 1:
                # first or only return, classified as "default"
                mask[idx] = 1
    pts = np.extract(mask, pts)

    # extract [x, y] and z arrays
    npts = len(pts)
    xy = np.zeros((npts, 2))
    zz = np.zeros(npts)
    for idx, pt in enumerate(pts):
        xy[idx, 0] = pt[0]
        xy[idx, 1] = pt[1]
        zz[idx] = pt[2]

    # construct KDTree
    tree = cKDTree(xy) 

    # find NN for all grid points
    xy_grd = np.hstack([x_grd.reshape((-1,1)), y_grd.reshape((-1,1))])
    nn_dist, nn_idx = tree.query(xy_grd, k=16)

    # compute local medians
    z_grd = np.median(zz[nn_idx], axis=1).reshape(x_grd.shape)

    return x_vec, y_vec, z_grd  # TODO: decide what outputs I need


def create_geotiff(filename, x_vec, y_vec, z_grd):
    """
    Write input array as GeoTiff raster
    
    Arguments:
        filename: string, path to write GeoTiff file
        x_vec, y_vec: numpy 1D arrays, x and y coordinate axes
        z_grd: numpy 2D array, elevation grid 

    Returns: Nothing, writes result to file
    """
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


def upload_geotiff(filename, clobber=False):
    """
    Upload GeoTiff file to database

    Command-line tool 'rastertopsql' used to generate SQL commands

    Arguments:
        filename: string, GeoTiff file to upload
        clobber: set True to drop existing table and create a new one, or False
            to append to the existing table
    
    Returns: Nothing
    """
    # generate sql commands
    if clobber:
        cmd = f'raster2pgsql -d -C -r -s {PRJ_SRID} -b 1 -t auto {filename} {RASTER_DB}'
    else:
        cmd = f'raster2pgsql -a -C -r -s {PRJ_SRID} -b 1 {filename} {RASTER_DB}'
    out = subprocess.run(cmd.split(' '), stdout=subprocess.PIPE, check=True)
    sql = out.stdout.decode('utf-8')

    # execute sql commands
    with connect_db() as conn:
        cur = conn.cursor()
        cur.execute(sql)
        cur.close()


def tile_limits(x_min, x_max, y_min, y_max, x_tile, y_tile):
    """
    Return list of bounding boxes for tiles within the specified range
    
    Arguments:
        x_min, x_max, y_min, y_max: floats, limits for the full region-of-interest
        x_tile, y_tile: floats, desired dimensions for generated tiles, note that
            the actual dimensions are adjusted to evenly divide the ROI
    
    Returns: list of bounding boxes, formatted as [[x0, x1], [y0, y1]]
    """
    # modify tile dimensions to a nice multiple of the bounding box
    x_rng = x_max - x_min
    x_num_tiles = x_rng // x_tile
    x_tile = x_rng / x_num_tiles 

    y_rng = y_max - y_min
    y_num_tiles = y_rng // y_tile
    y_tile = y_rng / y_num_tiles 

    # generate tile bboxes
    tiles = []
    for ii in range(x_num_tiles):
        for jj in range(y_num_tiles):
            x0 = x_min + ii*x_tile
            x1 = x0 + x_tile
            y0 = y_min + jj*y_tile
            y1 = y0 + y_tile
            tiles.append([[x0, x1], [y0, y1]])

    return tiles

