import json
from pkg_resources import resource_filename
from shutil import copyfile
import os

# load config dict
CONFIG_FILE = resource_filename('parasol', 'config.json')
CONFIG_FILE_DEFAULT = resource_filename('parasol', 'config.json.default')
if not os.path.isfile(CONFIG_FILE):
    print(f'Config file not found -- creating default file at: {CONFIG_FILE}')
    copyfile(CONFIG_FILE_DEFAULT, CONFIG_FILE)
with open(CONFIG_FILE, 'r') as fp:
    config = json.load(fp)

# unpack config constants
LIDAR_DB = config['LIDAR_DB']
GEO_SRID = config['GEO_SRID']
PRJ_SRID = config['PRJ_SRID']
LIDAR_TABLE = config['LIDAR_TABLE']
RASTER_DB = config['RASTER_DB']
SURFACE_TABLE = config['SURFACE_TABLE']
GROUND_TABLE = config['GROUND_TABLE']
BBOX_PRJ = config['BBOX_PRJ']
PSQL_USER = config['PSQL_USER']
PSQL_PASS = config['PSQL_PASS']
PSQL_HOST = config['PSQL_HOST']
PSQL_PORT = config['PSQL_PORT']

# setup environment variables for GRASS
os.environ['GISBASE'] = os.path.expanduser(config['GRASS_GISBASE'])
os.environ['GISRC'] = os.path.expanduser(config["GRASS_GISRC"])

# create grass configuration directory, if needed
if not os.path.isdir(os.path.dirname(os.environ['GISRC'])):
    os.makedirs(os.path.dirname(os.environ['GISRC']))

# create grass configuration file
with open(os.environ['GISRC'], 'w') as fp:
    fp.write(f'GISDBASE: {os.path.expanduser(config["GRASS_GISRC_GISDBASE"])}\n')
    fp.write(f'LOCATION_NAME: {config["GRASS_GISRC_LOCATION_NAME"]}\n')
    fp.write(f'MAPSET: {config["GRASS_GISRC_MAPSET"]}\n')

# load submodules
from parasol import lidar, raster

