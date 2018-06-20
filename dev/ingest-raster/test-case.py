"""
Exploratory code for creating and populating the raster database
"""

import parasol
import logging
from matplotlib import pyplot as plt
import numpy as np
import numpy as np
from osgeo import gdal
from osgeo import gdal_array
from osgeo import osr
import subprocess

logging.basicConfig(level=logging.INFO)

# # create a test raster, as a numpy array
# maxx = 335999.6937      
# maxy = 4696499.905      
# minx = 334499.6937
# miny = 4694999.905       
# xvec, yvec, zgrd = parasol.raster.grid_points(minx, maxx, miny, maxy)
# # plt.imshow(zgrd, cmap='hot', interpolation='nearest')
# # plt.show()

# # write to a geotiff
# parasol.raster.create_geotiff('test.tif', xvec, yvec, zgrd)

# # create and populate database
# parasol.raster.create_db(clobber=True)
# parasol.raster.upload_geotiff('test.tif', clobber=True)
# parasol.raster.upload_geotiff('test.tif', clobber=False) # fails due to constraints, which is good!

# create and populate database, tiled
maxx = 335999.6937      
maxy = 4696499.905      
minx = 334499.6937
miny = 4694999.905       

tiles = parasol.raster.tile_limits(minx, maxx, miny, maxy, 500, 500)

x_tiles = []
y_tiles = []
zz_tiles = []
z_min = 100000
z_max = -100000
for ii, tile in enumerate(tiles):
    print(f'Generating tile {ii} of {len(tiles)}')
    x, y, zz = parasol.raster.grid_points(**tile) # top only
    x_tiles.append(x)
    y_tiles.append(y)
    zz_tiles.append(zz)
    z_min = min(z_min, zz.min())
    z_max = max(z_max, zz.max())

# DEBUG: plot 
for jj in range(ii+1):
    x = x_tiles[jj]
    y = y_tiles[jj]
    zz = zz_tiles[jj]
    dx = (x[1]-x[0])/2.
    dy = (y[1]-y[0])/2.
    extent = [x[0]-dx, x[-1]+dx, y[0]-dy, y[-1]+dy]
    plt.imshow(zz, vmin=z_min, vmax=z_max, extent=extent, origin='lower', interpolation='nearest')
    xbox = [extent[0], extent[1], extent[1], extent[0], extent[0]]
    ybox = [extent[2], extent[2], extent[3], extent[3], extent[2]]
    plt.plot(xbox, ybox, color='k', linewidth=0.5, linestyle=':')
plt.colorbar()
plt.show()


# parasol.raster.create_db(clobber=True)
# parasol.raster.upload_geotiff('test.tif', clobber=True)
# parasol.raster.upload_geotiff('test.tif', clobber=False) # fails due to constraints, which is good!
