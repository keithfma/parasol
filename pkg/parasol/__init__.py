import json
from pkg_resources import resource_filename
from shutil import copyfile
import os
import subprocess
import pyproj
from argparse import Namespace

# load config dict
CONFIG_FILE = resource_filename('parasol', 'config.json')
CONFIG_FILE_DEFAULT = resource_filename('parasol', 'config.json.default')
if not os.path.isfile(CONFIG_FILE):
    print(f'Config file not found -- creating default file at: {CONFIG_FILE}')
    copyfile(CONFIG_FILE_DEFAULT, CONFIG_FILE)
with open(CONFIG_FILE, 'r') as fp:
    config = json.load(fp)

# compute domain limits in geographic coords
prj0 = pyproj.Proj(init=f'epsg:{config["PRJ_SRID"]}')
prj1 = pyproj.Proj(init=f'epsg:{config["GEO_SRID"]}')
ll = pyproj.transform(prj0, prj1, config["DOMAIN_XLIM"][0], config["DOMAIN_YLIM"][0])
lr = pyproj.transform(prj0, prj1, config["DOMAIN_XLIM"][1], config["DOMAIN_YLIM"][0])
ul = pyproj.transform(prj0, prj1, config["DOMAIN_XLIM"][0], config["DOMAIN_YLIM"][1])
ur = pyproj.transform(prj0, prj1, config["DOMAIN_XLIM"][1], config["DOMAIN_YLIM"][1])
lons = [ll[0], lr[0], ur[0], ul[0]]
lats = [ll[1], lr[1], ur[1], ul[1]]
config["DOMAIN_XLIM_GEO"] = [min(lons), max(lons)]
config["DOMAIN_YLIM_GEO"] = [min(lats), max(lats)]

# convert config to namespace for easy access
cfg = Namespace(**config)

# load submodules
from parasol import common, lidar, surface, shade, geoserver, osm, routing, server
