"""
Utility for selecting and downloading LiDAR data from https://coast.noaa.gov 
"""

# import shapefile
from osgeo import ogr
from shutil import copyfile

# constants
BND_SHP_FILE = '../shp/ma_community_bnd/data/TOWNSSURVEY_POLYM.shp'
STUDY_TOWNS = ['BROOKLINE', 'BOSTON', 'NEWTON', 'SOMERVILLE', 'WATERTOWN',
                    'BELMONT', 'CAMBRIDGE']
STUDY_SHP = '../shp/ma_community_bnd/munged/study_area.shp'

# TODO: load MA town boundaries and extract study area

# bnd_shp = shapefile.Reader(BND_SHP_FILE)
# study_objs = []
# for shp in bnd_shp.shapeRecords():
#     if shp.record[0] in STUDY_AREA_TOWNS:
#         study_area_objs.append(shp)
# 
# print(len(STUDY_AREA_TOWNS), len(study_area_objs))

bnd_shp = ogr.Open(BND_SHP_FILE)
bnd_layer = bnd_shp.GetLayer()
study_poly = ogr.Geometry(ogr.wkbPolygon)
for feature in bnd_layer:
    if feature['TOWN'] in STUDY_AREA_TOWNS:
        geom = feature.GetGeometryRef()
        study_poly = study_poly.Union(geom)

# TODO: load LiDAR (NOAA Post-Sandy) tiles

# TODO: get list of all tiles in study area

# TODO: download tiles one-at-a-time

# TODO: unpack and clean up
