"""
Shade data handlers
"""

import os
import subprocess
import logging
import argparse
from datetime import datetime
import numpy as np
import math
from pdb import set_trace
import requests
from pkg_resources import resource_filename

from parasol import surface, common, cfg


logger = logging.getLogger(__name__)


# local constants
STYLE_NAME = 'shade'


def init_grass():
    """Jump through all the hoops needed to run GRASS programatically"""

    # set required environment variables
    os.environ['GISBASE'] = cfg.GRASS_GISBASE
    os.environ['GISRC'] = cfg.GRASS_GISRC
    
    # create grass configuration directory, if needed
    if not os.path.isdir(os.path.dirname(cfg.GRASS_GISRC)):
        os.makedirs(os.path.dirname(cfg.GRASS_GISRC))
    
    # create grass configuration file
    with open(cfg.GRASS_GISRC, 'w') as fp:
        fp.write(f'GISDBASE: {cfg.GRASS_GISDBASE}\n')
        fp.write(f'LOCATION_NAME: {cfg.GRASS_LOCATION}\n')
        fp.write(f'MAPSET: {cfg.GRASS_MAPSET}\n')
        fp.write('GUI: wxpython\n')
    
    # # create database, location, and mapset folders, if needed
    if not os.path.isdir(cfg.GRASS_GISDBASE):
        os.makedirs(cfg.GRASS_GISDBASE)
    map_dir = f'{cfg.GRASS_GISDBASE}/{cfg.GRASS_LOCATION}/{cfg.GRASS_MAPSET}'
    subprocess.run(['grass74', '-c', f'EPSG:{cfg.PRJ_SRID}', '-e', map_dir])


def clear_grass():
    """Remove all working files from the GRASS database"""
    # subprocess.run(['grass', '--exec', 'g.remove', 'type=raster', f'pattern="*"'])
    raise NotImplementedError # works in Bash, fails to find files here, shelved as non-essential


def prep_inputs():
    """Prepare static inputs for insolation calculation in GRASS database"""
    
    # import surface and ground elevations
    surf_file = os.path.join(cfg.SURFACE_DIR, 'surface.tif')
    subprocess.run(['grass', '--exec', 'r.import', '--overwrite', 
        f'input={surf_file}', f'output=surface@{cfg.GRASS_MAPSET}']) 

    grnd_file = os.path.join(cfg.SURFACE_DIR, 'ground.tif')
    subprocess.run(['grass', '--exec', 'r.import', '--overwrite', 
        f'input={grnd_file}', f'output=ground@{cfg.GRASS_MAPSET}']) 

    # set compute region -- very important!
    subprocess.run(['g.region', f'raster=surface@{cfg.GRASS_MAPSET}']) 
    
    # compute constant shade component (e.g., under trees, within buildings
    mapcalc_expression = f'"shade-mask@{cfg.GRASS_MAPSET}" = ("surface@{cfg.GRASS_MAPSET}"-"ground@{cfg.GRASS_MAPSET}")>3'
    subprocess.run(['r.mapcalc', f'expression={mapcalc_expression}', '--overwrite'])

    # generate ancillary inputs needed for solar calc
    subprocess.run(['grass', '--exec', 'r.slope.aspect', '--overwrite',
        f'elevation=surface@{cfg.GRASS_MAPSET}', 'slope=slope', f'aspect=aspect'])
    subprocess.run(['grass', '--exec', 'r.latlong', '--overwrite',
        f'input=surface@{cfg.GRASS_MAPSET}', 'output=lat'])              
    subprocess.run(['grass', '--exec', 'r.latlong', '--overwrite', 
        f'input=surface@{cfg.GRASS_MAPSET}', '-l', 'output=lon'])              


def insolation(day, hour, file_name):
    """
    Compute insolation (W/m2) raster within ROI for specified time 
    
    Arguments:
        day: int, day of the year 
        hour: local solar time, decimal hours
        file_name: string, path to save retults as geotiff
    """
    # get name for GRASS layer
    layer_name = os.path.splitext(os.path.basename(file_name))[0]

    # set compute region -- very important!
    subprocess.run(['g.region', f'raster=surface@{cfg.GRASS_MAPSET}']) 

    # solar calculation
    logger.info(f'Computing insolation for day={day}, time={hour}')
    subprocess.run(['grass', '--exec', 'r.sun', f'time={hour}', f'day={day}',
        f'elevation=surface@{cfg.GRASS_MAPSET}', f'aspect=aspect@{cfg.GRASS_MAPSET}',
        f'slope=slope@{cfg.GRASS_MAPSET}', f'glob_rad={layer_name}@{cfg.GRASS_MAPSET}',
        '--overwrite'])

    # compute minimum insolation
    result = subprocess.run(['grass', '--exec', 'r.info', '-r',
        f'map={layer_name}@{cfg.GRASS_MAPSET}'], stdout=subprocess.PIPE)
    min_line = result.stdout.decode('utf-8').split()[0]
    min_value = float(min_line.split('=')[1])

    # apply minimum insolation where surface is above the ground (trees, buildings)
    if_str = f'if( "shade-mask", {min_value}, "{layer_name}@{cfg.GRASS_MAPSET}" )'
    subprocess.run(['r.mapcalc', f'expression="{layer_name}@{cfg.GRASS_MAPSET}" = {if_str}', '--overwrite'])

    # dump results to file
    logger.info(f'Saving insolation as "{file_name}"')
    subprocess.run(['grass', '--exec', 'r.out.gdal', f'input={layer_name}@{cfg.GRASS_MAPSET}',
        f'output={file_name}', 'format=GTiff', '-c', '--overwrite'])
    
    # delete the temporary layer in the GRASS DB
    # TODO: fails to find layer, not clear why
    subprocess.run(['grass', '--exec', 'g.remove', '-f', 'type=raster',
        f'pattern="{layer_name}"'])


# TODO: explore multiprocessing
def update_today():
    """Update insolation frames for whole day in loop"""

    # get current day and list of times (interval, etc, are set using config variables)
    day = int(datetime.now().strftime('%j'))
    times = np.arange(cfg.SHADE_START_HOUR, cfg.SHADE_STOP_HOUR, cfg.SHADE_INTERVAL_HOUR)
    
    # create output directory, if needed
    if not os.path.isdir(cfg.SHADE_DIR):
        os.makedirs(cfg.SHADE_DIR)

    for ii, time in enumerate(times): 
        logger.info(f'Update daily insolation, time step {ii} of {len(times)}')
        time_hour = math.floor(time)
        time_min = round((time - time_hour)*60)
        name = os.path.join(cfg.SHADE_DIR,
            'today_{:02d}{:02d}.tif'.format(time_hour, time_min))
        insolation(day, time, name)


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


# NOTE: no periods in store names!


def add_geoserver_layer(tif_file):
    """
    Upload shade layer definition to geoserver
    """
    # create coveragestore
    # note: may fail if style exists already, which is fine
    store_name = os.path.basename(os.path.splitext(tif_file)[0])
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

    # TODO: create layer
    url = url + '/coverages'
    hdr = {'Content-type': 'application/json'}
    data = {
        'coverage': {
            "name": store_name,
            "title": store_name,
            "srs": "EPSG:32619"
            }
        }
    resp = requests.post(url, headers=hdr, auth=auth, json=data)
    return resp
    

# curl -u admin:geoserver -v -XPOST -H 'Content-type: text/xml' \
#       -d '<coverage>
#           <name>imageGeoTiffWGS84</name>
#           <title>imageGeoTiffWGS84</title>
#           <nativeCRS>GEOGCS[&quot;WGS 84&quot;,DATUM[&quot;World Geodetic System 1984&quot;,SPHEROID[&quot;WGS 84&quot;,6378137.0, 298.257223563, AUTHORITY[&quot;EPSG&quot;,&quot;7030&quot;]],AUTHORITY[&quot;EPSG&quot;,&quot;6326&quot;]],PRIMEM[&quot;Greenwich&quot;, 0.0, AUTHORITY[&quot;EPSG&quot;,&quot;8901&quot;]],UNIT[&quot;degree&quot;, 0.017453292519943295],AXIS[&quot;Geodetic longitude&quot;, EAST],AXIS[&quot;Geodetic latitude&quot;, NORTH],AUTHORITY[&quot;EPSG&quot;,&quot;4326&quot;]]</nativeCRS>
#           <srs>EPSG:4326</srs>
#           <latLonBoundingBox><minx>-179.958</minx><maxx>-105.002</maxx><miny>-65.007</miny><maxy>65.007</maxy><crs>EPSG:4326</crs></latLonBoundingBox>
#           </coverage>' \
#       "http://localhost:8080/geoserver/rest/workspaces/wsgeotiff/coveragestores/wsgeotiff_imageGeoTiffWGS84_1298678792699/coverages"
    


# command line utilities -----------------------------------------------------


def initialize_cli():
    """Command line utility to init inputs for shade calculations"""
    ap = argparse.ArgumentParser(
        description="Initialize Parasol surface & ground raster databases - clobbers existing!",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter) 
    ap.add_argument('--log', type=str, default='info', help="select logging level",
                    choices=['debug', 'info', 'warning', 'error', 'critical'])
    args = ap.parse_args()

    log_lvl = getattr(logging, args.log.upper())
    logging.basicConfig(level=log_lvl)
    logger.setLevel(log_lvl)

    init_grass()
    prep_inputs()


def update_cli():
    """Command line utility to init inputs for shade calculations"""
    ap = argparse.ArgumentParser(
        description="Update daily insolation rasters - clobbers existing!",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter) 
    ap.add_argument('--log', type=str, default='info', help="select logging level",
                    choices=['debug', 'info', 'warning', 'error', 'critical'])
    args = ap.parse_args()

    log_lvl = getattr(logging, args.log.upper())
    logging.basicConfig(level=log_lvl)
    logger.setLevel(log_lvl)

    update_today()


# TODO: CLI for computing a validation scene
