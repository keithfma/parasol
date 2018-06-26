import json
from pkg_resources import resource_filename
from shutil import copyfile
import os
import subprocess
from argparse import Namespace

# load config dict
CONFIG_FILE = resource_filename('parasol', 'config.json')
CONFIG_FILE_DEFAULT = resource_filename('parasol', 'config.json.default')
if not os.path.isfile(CONFIG_FILE):
    print(f'Config file not found -- creating default file at: {CONFIG_FILE}')
    copyfile(CONFIG_FILE_DEFAULT, CONFIG_FILE)
with open(CONFIG_FILE, 'r') as fp:
    config = json.load(fp)
cfg = Namespace(**config)


# load submodules
from parasol import common
from parasol import lidar
from parasol import surface
from parasol import shade
from parasol import geoserver
from parasol import osm

