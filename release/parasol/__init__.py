import json
from pkg_resources import resource_filename
from shutil import copyfile
import os
import subprocess

# load config dict
CONFIG_FILE = resource_filename('parasol', 'config.json')
CONFIG_FILE_DEFAULT = resource_filename('parasol', 'config.json.default')
if not os.path.isfile(CONFIG_FILE):
    print(f'Config file not found -- creating default file at: {CONFIG_FILE}')
    copyfile(CONFIG_FILE_DEFAULT, CONFIG_FILE)
with open(CONFIG_FILE, 'r') as fp:
    config = json.load(fp)

# unpack config constants
DATA_DIR = os.path.expanduser(config['DATA_DIR'])
DOMAIN_XLIM = config['DOMAIN_XLIM']
DOMAIN_YLIM = config['DOMAIN_YLIM']
LIDAR_DB = config['LIDAR_DB']
GEO_SRID = config['GEO_SRID']
PRJ_SRID = config['PRJ_SRID']
LIDAR_TABLE = config['LIDAR_TABLE']
BBOX_PRJ = config['BBOX_PRJ']
PSQL_USER = config['PSQL_USER']
PSQL_PASS = config['PSQL_PASS']
PSQL_HOST = config['PSQL_HOST']
PSQL_PORT = config['PSQL_PORT']
GRASS_GISBASE = os.path.expanduser(config["GRASS_GISBASE"])
GRASS_GISRC = os.path.expanduser(config["GRASS_GISRC"])
GRASS_GISDBASE = os.path.expanduser(config["GRASS_GISDBASE"])
GRASS_LOCATION = config["GRASS_LOCATION"]
GRASS_MAPSET = config["GRASS_MAPSET"]

# create data folder, if needed
if not os.path.isdir(DATA_DIR):
    os.makedirs(DATA_DIR)

# setup environment variables for GRASS
os.environ['GISBASE'] = GRASS_GISBASE
os.environ['GISRC'] = GRASS_GISRC

# create grass configuration directory, if needed
if not os.path.isdir(os.path.dirname(GRASS_GISRC)):
    os.makedirs(os.path.dirname(GRASS_GISRC))

# create grass configuration file
with open(GRASS_GISRC, 'w') as fp:
    fp.write(f'GISDBASE: {GRASS_GISDBASE}\n')
    fp.write(f'LOCATION_NAME: {GRASS_LOCATION}\n')
    fp.write(f'MAPSET: {GRASS_MAPSET}\n')
    fp.write('GUI: wxpython\n')

# create database, location, and mapset folders, if needed
subprocess.run(['grass74', '-c', f'EPSG:{PRJ_SRID}', '-e',
    f'{GRASS_GISDBASE}/{GRASS_LOCATION}/{GRASS_MAPSET}'])

# load submodules
from parasol import common
from parasol import lidar
from parasol import surface
from parasol import shade

