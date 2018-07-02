"""
Geoserver config automation
"""

import argparse
import logging
import requests
from pkg_resources import resource_filename
import os
import glob

from parasol import cfg


logger = logging.getLogger(__name__)


# local constants
STYLE_NAME = 'shade'


def add_geoserver_workspace():
    """
    Create geoserver workspace

    See guide at: http://docs.geoserver.org/stable/en/user/rest/workspaces.html
    """
    # note: may fail if workspace exists already, which is fine
    url = f'http://{cfg.GEOSERVER_HOST}:{cfg.GEOSERVER_PORT}/geoserver/rest/workspaces'
    hdr = {"Content-type": "text/xml"}
    auth = (cfg.GEOSERVER_USER, cfg.GEOSERVER_PASS)
    resp = requests.post(url, headers=hdr, auth=auth, 
        data=f"<workspace><name>{cfg.GEOSERVER_WORKSPACE}</name></workspace>")


def add_geoserver_style():
    """
    Upload shade layer style definition to geoserver

    See guide at: http://docs.geoserver.org/stable/en/user/rest/styles.html
    """
    # create style
    # note: may fail if style exists already, which is fine
    url = f'http://{cfg.GEOSERVER_HOST}:{cfg.GEOSERVER_PORT}/geoserver/rest/styles'
    hdr = {"Content-type": "application/json"}
    auth = (cfg.GEOSERVER_USER, cfg.GEOSERVER_PASS)
    data = {
        "style": {
            "name": STYLE_NAME,
            "workspace": {
                "name": cfg.GEOSERVER_WORKSPACE,
            },
            "format": "sld",
            "languageVersion": {
                "version": "1.0.0"
            },
            "filename": f"{STYLE_NAME}.sld"
        }
    }
    resp = requests.post(url, auth=auth, json=data, headers=hdr)

    # update style definition
    url = f'http://{cfg.GEOSERVER_HOST}:{cfg.GEOSERVER_PORT}/geoserver/rest/workspaces/{cfg.GEOSERVER_WORKSPACE}/styles/{STYLE_NAME}.xml'
    hdr = {"Content-type": "application/vnd.ogc.sld+xml"}
    auth = (cfg.GEOSERVER_USER, cfg.GEOSERVER_PASS)
    style_file = resource_filename('parasol', os.path.join('templates', 'shade.sld'))
    with open(style_file, 'r') as fp:
        resp = requests.put(url, auth=auth, headers=hdr, data=fp.read())
    resp.raise_for_status()



# NOTE: no periods in store names! This seems to cause problems
def add_geoserver_layer(tif_file):
    """
    Upload shade layer definition to geoserver
    """
    # create coveragestore
    # note: may fail if style exists already, which is fine
    store_name = os.path.basename(os.path.splitext(tif_file)[0])
    layer_name = store_name
    url = f'http://{cfg.GEOSERVER_HOST}:{cfg.GEOSERVER_PORT}/geoserver/rest/workspaces/{cfg.GEOSERVER_WORKSPACE}/coveragestores'
    auth = (cfg.GEOSERVER_USER, cfg.GEOSERVER_PASS)
    hdr = {'Content-type': 'application/json'}    
    data =  {
        "coverageStore": {
            "name": store_name,
            "type": "GeoTIFF",
            "enabled": True,
            "workspace": {
                "name": cfg.GEOSERVER_WORKSPACE,
            },
            "_default": False,
            "url": f"file:{tif_file}",
      }
    }
    resp = requests.post(url, headers=hdr, auth=auth, json=data)
    
    # add data to store
    # note: basically the same as the create command, except the method and
    #   url, needed in case the store exists already
    url = url + '/' + store_name
    resp = requests.put(url, headers=hdr, auth=auth, json=data)
    resp.raise_for_status()

    # create layer
    url = url + '/coverages'
    hdr = {'Content-type': 'application/json'}
    data = {
        'coverage': {
            "name": layer_name,
            "title": layer_name,
            "srs": "EPSG:32619",
            }
        }
    resp = requests.post(url, headers=hdr, auth=auth, json=data)

    # set layer style
    url = f'http://{cfg.GEOSERVER_HOST}:{cfg.GEOSERVER_PORT}/geoserver/rest/workspaces/{cfg.GEOSERVER_WORKSPACE}/layers/{layer_name}'
    hdr = {'Content-type': 'application/json'}    
    data =  {
        "layer": {
            "defaultStyle": {
                "workspace": cfg.GEOSERVER_WORKSPACE,
                "name": STYLE_NAME,
                }
            }
        }
    resp = requests.put(url, headers=hdr, auth=auth, json=data)

    return resp


def init_geoserver():
    """Initialize geoserver workspace, layers, and style"""
    add_geoserver_workspace()
    add_geoserver_style()
    for fn in glob.glob(os.path.join(cfg.SHADE_DIR, 'bot_*.tif')):
        add_geoserver_layer(fn)
    for fn in glob.glob(os.path.join(cfg.SHADE_DIR, 'top_*.tif')):
        add_geoserver_layer(fn)


def initialize_geoserver_cli():
    """Command line utility to init geoserver layers"""
    ap = argparse.ArgumentParser(
        description="Initialize Parasol geoserver layers - clobbers existing!",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter) 
    ap.add_argument('--log', type=str, default='info', help="select logging level",
                    choices=['debug', 'info', 'warning', 'error', 'critical'])
    args = ap.parse_args()

    log_lvl = getattr(logging, args.log.upper())
    logging.basicConfig(level=log_lvl)
    logger.setLevel(log_lvl)

    init_geoserver()
