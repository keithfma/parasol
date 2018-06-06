"""
Utility for selecting and downloading LiDAR data from https://coast.noaa.gov 
"""

from osgeo import ogr
import os
import wget

# gather list of tile urls
shp = ogr.Open('../noaa_lidar_index/deriv/study_area.shp')
layer = shp.GetLayer()
urls = [feature['URL'].strip() for feature in layer]

# create dist directory
if not os.path.isdir('dist'):
    os.makedirs('dist')

# download tiles one-at-a-time
for ii, url in enumerate(urls):
    print('Downloading tile {}/{} from {}'.format(ii, len(urls), url))
    wget.download(url, out='dist')

# TODO: unpack and clean up
