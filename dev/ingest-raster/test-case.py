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
# parasol.raster.to_geotiff('test.tif', xvec, yvec, zgrd)

# create and populate database
parasol.raster.create_db(clobber=True)

# read in first file (includes -d and -t options)
cmd = f'raster2pgsql -d -C -r -s {parasol.LIDAR_PRJ_SRID} -b 1 -t auto test.tif {parasol.RASTER_DB}'
out = subprocess.run(cmd.split(' '), stdout=subprocess.PIPE, check=True)
sql = out.stdout.decode('utf-8')

with parasol.raster.connect_db() as conn:
    cur = conn.cursor()
    cur.execute(sql)
    cur.close()

# read in another (well, the same one again)

