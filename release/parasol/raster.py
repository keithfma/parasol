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
from pdb import set_trace


from parasol import lidar
from parasol import RASTER_DB, PSQL_USER, PSQL_PASS, PSQL_HOST, PSQL_PORT, PRJ_SRID
# TODO: need separate DB for top, bottom, shade rasters
# TODO: should I project or just stay in geographic coords?


logger = logging.getLogger(__name__)


# constants
RESOLUTION = 1 # meters
PAD = 10 # meters


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

    # build output grid spanning bbox
    x_vec = np.arange(math.floor(x_min), math.floor(x_max), RESOLUTION)   
    y_vec = np.arange(math.floor(y_min), math.floor(y_max), RESOLUTION)   
    x_grd, y_grd = np.meshgrid(x_vec, y_vec)

    # retrieve data, including a pad on all sides
    pts = lidar.retrieve(x_min-PAD, y_min-PAD, x_max+PAD, y_max+PAD)

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

    return x_vec, y_vec, z_grd


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
        # cmd = f'raster2pgsql -d -C -r -s {PRJ_SRID} -b 1 -t auto {filename} {RASTER_DB}'
        cmd = f'raster2pgsql -d -s {PRJ_SRID} -b 1 -t auto {filename} {RASTER_DB}'
    else:
        # cmd = f'raster2pgsql -a -C -r -s {PRJ_SRID} -b 1 {filename} {RASTER_DB}'
        cmd = f'raster2pgsql -a -s {PRJ_SRID} -b 1 {filename} {RASTER_DB}'
    out = subprocess.run(cmd.split(' '), stdout=subprocess.PIPE, check=True)
    sql = out.stdout.decode('utf-8')
    
    # DEBUG
    with open('delete_me.sql', 'w') as fp:
        fp.write(sql)

    # execute sql commands
    with connect_db() as conn:
        cur = conn.cursor()
        cur.execute(sql)
        cur.close()


def register_raster():
    """
    SELECT AddRasterConstraints('myrasters'::name, 'rast'::name);
    """
    with connect_db() as conn:
        cur = conn.cursor()
        cur.execute("SELECT AddRasterConstraints('','parasol_raster','rast',TRUE,TRUE,TRUE,TRUE,TRUE,TRUE,TRUE,TRUE,TRUE,TRUE,TRUE,TRUE);")


def tile_limits(x_min, x_max, y_min, y_max, x_tile, y_tile):
    """
    Return list of bounding boxes for tiles within the specified range
    
    Arguments:
        x_min, x_max, y_min, y_max: floats, limits for the full region-of-interest
        x_tile, y_tile: floats, desired dimensions for generated tiles, note that
            the actual dimensions are adjusted to evenly divide the ROI
    
    Returns: list of bounding boxes, each a dict with fields x_min, x_max, y_min, y_max
    """
    # modify the bounding box to be a multiple of the tile dimension
    x_pad = (x_max - x_min) % x_tile
    x_min += math.ceil(x_pad/2)
    x_max += math.floor(x_pad/2) 
    x_num_tiles = int((x_max - x_min) // x_tile)

    y_pad = (y_max - y_min) % y_tile
    y_min += math.ceil(y_pad/2)
    y_max += math.floor(y_pad/2) 
    y_num_tiles = int((y_max - y_min) // y_tile)

    # generate tile bboxes
    tiles = []
    for ii in range(x_num_tiles):
        for jj in range(y_num_tiles):
            tile = {}
            tile['x_min'] = x_min + ii*x_tile
            tile['x_max'] = tile['x_min'] + x_tile
            tile['y_min'] = y_min + jj*y_tile
            tile['y_max'] = tile['y_min'] + y_tile
            tiles.append(tile)

    return tiles


# TODO: write top, bot, and shade as bands, or in separate tables?
def upload_tiles(x_min, x_max, y_min, y_max, x_tile, y_tile, clobber=False):
    """
    Generate rasters and upload to database, tile-by-tile

    Arguments:
        x_min, x_max, y_min, y_max: floats, limits for the full region-of-interest
        x_tile, y_tile: floats, desired dimensions for generated tiles, note that
            the actual dimensions are adjusted to evenly divide the ROI
        clobber: set True to drop existing table and create a new one, or False
            to append to the existing table
    
    Returns: nothing
    """
    TIF_FILE = 'delete_me.tif' # TODO: use tempfiles

    tiles = tile_limits(x_min, x_max, y_min, y_max, x_tile, y_tile)
    num_tiles = len(tiles)

    for ii, tile in enumerate(tiles):
        print(f'Generating tile {ii+1} of {num_tiles}')
        x_vec, y_vec, z_grd = grid_points(**tile) # DEBUG: top only
        print(f'X: [{x_vec[0]}, {x_vec[-1]}], Y: [{y_vec[0]}, {y_vec[-1]}]')
        create_geotiff(TIF_FILE, x_vec, y_vec, z_grd)
        upload_geotiff(TIF_FILE, clobber=(clobber and ii==0))
        print(f'Uploaded tile {ii+1} of {num_tiles}')


