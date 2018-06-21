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

# # create a test raster, as a numpy array ------------------
# maxx = 335999.6937      
# maxy = 4696499.905      
# minx = 334499.6937
# miny = 4694999.905       
# xvec, yvec, zgrd = parasol.raster.grid_points(minx, maxx, miny, maxy)
# # plt.imshow(zgrd, cmap='hot', interpolation='nearest')
# # plt.show()
# 
# # write to a geotiff
# parasol.raster.create_geotiff('test.tif', xvec, yvec, zgrd)

# # create and populate database using test raster ------------
# parasol.raster.create_db(clobber=True)
# parasol.raster.upload_geotiff('test.tif', clobber=True)
# parasol.raster.register_raster()

# # create and populate database, tiled ------------------
# x_min = 334499.6937
# x_max = 335999.6937      
# y_min = 4694999.905       
# y_max = 4695509.905      
# x_tile = 500
# y_tile = 500
# 
# parasol.raster.create_db(clobber=True)
# parasol.raster.new(x_min, x_max, y_min, y_max, x_tile, y_tile)

# retrieve part of the raster ingested above
x_min = 327516
x_max = x_min + 1000 
y_min = 4692153
y_max = y_min + 1000
parasol.surface.retrieve(x_min, x_max, y_min, y_max, 'surface')

# zs, zg = parasol.raster.retrieve_numpy(x_min, x_max, y_min, y_max, plot=True)

# the same, but writing to files instead of retrieving array
# parasol.raster.retrieve_geotiff('delete_me', x_min, x_max, y_min, y_max)



