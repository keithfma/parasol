"""
Flask server for Parasol API/UI
"""

import flask
import argparse
import os
from pkg_resources import resource_filename
import psycopg2
from pdb import set_trace
import logging
from datetime import datetime
import jinja2
import subprocess
import shutil

from parasol import cfg, common, routing


logger = logging.getLogger(__name__)

# create app
app = flask.Flask('parasol')


# endpoints ------------------------------------------------------------------


@app.route('/', methods=["GET"])
def main():
    """Main Parasol user interface"""
    return flask.render_template('index.html')


def _route_response(length, sun, geojson):
    """Shared utility to format route data as JSON without parsing it"""
    data = f'{{ "length": {length}, "sun": {sun}, "route": {geojson} }}'
    return flask.Response(status=200, response=data, mimetype='application/json')


def _validate_endpoint(lon, lat):
    """Confirm that endpoint is in the domain limits"""
    valid = True
    if lon < cfg.DOMAIN_XLIM_GEO[0] or lon > cfg.DOMAIN_XLIM_GEO[1]:
        valid = False
    elif lat < cfg.DOMAIN_YLIM_GEO[0] or lat > cfg.DOMAIN_YLIM_GEO[1]:
        valid = False
    return valid


@app.route('/route/optimal', methods=['GET'])
def optimal():
    """
    Compute optimal (wrt sun/shade) route between specified start and end points

    Parameters (URL query string):
        lat0, lon0: floats, start point latitude, longitude
        lat1, lon1: floats, end point latitude, longitude
        beta: float, sun/shade preference parameter 
        hour, minute: ints, time to compute route for

    Returns: JSON object with fields:
        length: route length in meters
        sun: route solar cost in normalized units
        route: route line as geoJSON
    """
    lat0 = float(flask.request.args.get('lat0'))
    lon0 = float(flask.request.args.get('lon0'))
    lat1 = float(flask.request.args.get('lat1'))
    lon1 = float(flask.request.args.get('lon1'))
    beta = float(flask.request.args.get('beta'))
    hour = int(flask.request.args.get('hour'))
    minute = int(flask.request.args.get('minute'))

    # return status if outside domain
    if not _validate_endpoint(lon0, lat0) or not _validate_endpoint(lon1, lat1):
        return flask.Response(status=403)

    time = datetime.now().replace(
        hour=hour, minute=minute, second=0, microsecond=0)
    length, sun, geojson = routing.route_optimal(lon0, lat0, lon1, lat1, time, beta)

    return _route_response(length, sun, geojson)


@app.route('/route/shortest', methods=['GET'])
def shortest():
    """
    Compute shortest route between specified start and end points

    Parameters (URL query string):
        lat0, lon0: floats, start point latitude, longitude
        lat1, lon1: floats, end point latitude, longitude
        hour, minute: ints, time to compute route for

    Returns: JSON object with fields:
        length: route length in meters
        sun: route solar cost in normalized units
        route: route line as geoJSON
    """
    lat0 = float(flask.request.args.get('lat0'))
    lon0 = float(flask.request.args.get('lon0'))
    lat1 = float(flask.request.args.get('lat1'))
    lon1 = float(flask.request.args.get('lon1'))
    hour = int(flask.request.args.get('hour'))
    minute = int(flask.request.args.get('minute'))

    # return status if outside domain
    if not _validate_endpoint(lon0, lat0) or not _validate_endpoint(lon1, lat1):
        return flask.Response(status=403)

    time = datetime.now().replace(
        hour=hour, minute=minute, second=0, microsecond=0)
    length, sun, geojson = routing.route_shortest(lon0, lat0, lon1, lat1, time)

    return _route_response(length, sun, geojson)


@app.route('/layers', methods=['GET'])
def shade_layers_meta():
    """
    List available shade layer details

    Arguments: None

    Returns: JSON, list of available shade layers, each an object with fields:
        hour: int, hour for layer time
        minute: int, minute for layer time
        url: string, URL for tile layer, can be added to leaflet 
        params: object, URL query parameters
    """
    layers = []
    for this in common.shade_meta():
        layer = {}
        layer['hour'] = this['hour']
        layer['minute'] = this['minute']
        layer['url'] = f'http://{cfg.GEOSERVER_HOST}:{cfg.GEOSERVER_PORT}/geoserver/ows'
        layer['params'] = {
            'layers': f'{cfg.GEOSERVER_WORKSPACE}:{this["top"]}',
            'opacity': 0.7,
            }
        layers.append(layer)
    return flask.jsonify(layers)


# command line ---------------------------------------------------------------


def cli():
    """Run Parasol on localhost with Flask built-in server"""
    ap = argparse.ArgumentParser(
        description='Parasol Navigation - Debug Server, DO NOT DEPLOY',
        formatter_class= argparse.ArgumentDefaultsHelpFormatter)
    ap.add_argument('--debug', action='store_true',
        help='run server in "debug mode"')
    ap.add_argument('--host', type=str, default='0.0.0.0',
        help='hostname for flask server')
    ap.add_argument('--port', type=int, default=5000,
        help='server port number')
    ap.add_argument('--log', type=str, default='info', help="select logging level",
                    choices=['debug', 'info', 'warning', 'error', 'critical'])
    args = ap.parse_args()

    log_lvl = getattr(logging, args.log.upper())
    logging.basicConfig(level=log_lvl)
    logger.setLevel(log_lvl)

    app.run(host=args.host, port=args.port, debug=args.debug)


def deploy():
    """Initialize deployed server by creating and copying config files"""

    ap = argparse.ArgumentParser(
        description='Parasol Navigation: Initialize deployed Apache server',
        formatter_class= argparse.ArgumentDefaultsHelpFormatter)
    ap.add_argument('--venv', default=None, 
        help='Path to virtual environment where "parasol" package is installed')
    ap.add_argument('--user', default=cfg.APACHE_USER,
        help='User that will be used to run the server process')
    ap.add_argument('--group', default=cfg.APACHE_USER,
        help='Group that will be used to run the server process')
    ap.add_argument('--wsgi_path', default='/var/www/parasol', 
        help='Path to install WSGI script to')
    ap.add_argument('--conf_path', default='/etc/apache2/sites-available/',
        help='Path to Apache2 sites-available directory')
    ap.add_argument('--server_name', default=None,
        help='Server name (e.g. example.com) for Apache conf file')
 
    args = ap.parse_args()

    # create folders
    if not os.path.isdir(args.wsgi_path):
        os.makedirs(args.wsgi_path)

    # init Jinja
    jenv = jinja2.Environment(loader=jinja2.PackageLoader('parasol', 'templates'))

    # generate WSGI script
    wsgi = jenv.get_template('parasol.wsgi')
    wsgi_txt = wsgi.render(venv=args.venv)
    wsgi_file = os.path.join(args.wsgi_path, 'parasol.wsgi')
    with open(wsgi_file, 'w') as fp:
        fp.write(wsgi_txt)

    # update ownership and permissions
    shutil.chown(args.wsgi_path, args.user, args.group)
    shutil.chown(wsgi_file, args.user, args.group)
    subprocess.run(['chmod', '755', wsgi_file]) 

    # generate Apache config file
    conf = jenv.get_template('parasol.conf')
    conf_txt = conf.render(user=args.user, group=args.group,
        wsgi_path=args.wsgi_path, wsgi_file=wsgi_file,
        server_name=args.server_name)
    conf_file = os.path.join(args.conf_path, 'parasol.conf')
    with open(conf_file, 'w') as fp:
        fp.write(conf_txt)
