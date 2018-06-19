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
# # see: https://gis.stackexchange.com/questions/37238/writing-numpy-array-to-raster-file
# # BUG: tiff is not completely populated
# xmin = min(xvec)
# xmax = max(xvec)
# ymin = min(yvec)
# ymax = max(yvec)
# nrows, ncols = np.shape(zgrd)
# geotransform = (xmin, 1, 0, ymax, 0, -1)   
# output_raster = gdal.GetDriverByName('GTiff').Create('myraster.tif', ncols, nrows, 1, gdal.GDT_Float32)  # Open the file
# output_raster.SetGeoTransform(geotransform)  # Specify its coordinates
# srs = osr.SpatialReference()                 # Establish its coordinate encoding
# srs.ImportFromEPSG(parasol.LIDAR_PRJ_SRID)    
# output_raster.SetProjection( srs.ExportToWkt() )   # Exports the coordinate system 
# output_raster.GetRasterBand(1).WriteArray(zgrd)   # Writes my array to the raster
# output_raster.FlushCache()


# # write to a geotiff
# # see: https://pcjericks.github.io/py-gdalogr-cookbook/raster_layers.html#create-raster-from-array
def array2raster(newRasterfn,rasterOrigin,pixelWidth,pixelHeight,array):

    cols = array.shape[1]
    rows = array.shape[0]
    originX = rasterOrigin[0]
    originY = rasterOrigin[1]

    driver = gdal.GetDriverByName('GTiff')
    outRaster = driver.Create(newRasterfn, cols, rows, 1, gdal.GDT_Byte)
    outRaster.SetGeoTransform((originX, pixelWidth, 0, originY, 0, pixelHeight))
    outband = outRaster.GetRasterBand(1)
    outband.WriteArray(array)
    outRasterSRS = osr.SpatialReference()
    outRasterSRS.ImportFromEPSG(4326)
    outRaster.SetProjection(outRasterSRS.ExportToWkt())
    outband.FlushCache()


def main(newRasterfn,rasterOrigin,pixelWidth,pixelHeight,array):
    reversed_arr = array[::-1] # reverse array so the tif looks like the array
    array2raster(newRasterfn,rasterOrigin,pixelWidth,pixelHeight,reversed_arr) # convert array to raster


rasterOrigin = (-123.25745,45.43013)
pixelWidth = 10
pixelHeight = 10
newRasterfn = 'test.tif'
array = np.array([[ 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
                  [ 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
                  [ 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 1, 0, 1, 1, 1],
                  [ 1, 0, 1, 1, 1, 1, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 1, 1],
                  [ 1, 0, 1, 0, 0, 1, 1, 0, 1, 0, 1, 0, 0, 0, 1, 0, 1, 1, 1],
                  [ 1, 0, 1, 1, 0, 1, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 1, 1],
                  [ 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 1, 0, 1, 0, 0, 0, 1],
                  [ 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
                  [ 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
                  [ 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1]])
main(newRasterfn,rasterOrigin,pixelWidth,pixelHeight,array)

# # create and populate database
# parasol.raster.create_db(clobber=True)

