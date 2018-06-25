"""
Flask server for Parasol API/UI
"""

import flask
import argparse
import os
from pkg_resources import resource_filename
import psycopg2
from pdb import set_trace

from parasol import cfg


# create app
app = flask.Flask('parasol')


# endpoints ------------------------------------------------------------------


@app.route('/', methods=["GET"])
@app.route('/ui', methods=["GET"])
def main():
    """Main Parasol user interface"""
    return flask.render_template('index.html')


@app.route('/route', methods=['GET'])
def route():
    """
    Compute route between specified start and end points

    Parameters (URL query string):
        lat0, lon0 = floats, start point latitude, longitude
        lat1, lon1 = floats, end point latitude, longitude

    Returns: optimal route as geoJSON
    """
    # parse endpoints
    lat0 = float(flask.request.args.get('lat0'))
    lon0 = float(flask.request.args.get('lon0'))
    lat1 = float(flask.request.args.get('lat1'))
    lon1 = float(flask.request.args.get('lon1'))
   
    # connect to Postgresql database 
    conn = psycopg2.connect(f"dbname={cfg.OSM_DB} user={cfg.PSQL_USER}")
    cur = conn.cursor()
    
    # find start vertex
    cur.execute("SELECT id FROM ways_vertices_pgr ORDER BY the_geom <-> ST_SetSRID(ST_Point(%s, %s), 4326) LIMIT 1;",
                (lon0, lat0))
    start_id = cur.fetchone()[0]

    # find end vertex
    cur.execute("SELECT id FROM ways_vertices_pgr ORDER BY the_geom <-> ST_SetSRID(ST_Point(%s, %s), 4326) LIMIT 1;",
                (lon1, lat1))
    end_id = cur.fetchone()[0]

    # compute route, return GeoJSON for edges
    sql ='SELECT gid AS id, source, target, length AS cost, the_geom FROM ways'
    cur.execute(f"SELECT ST_AsGeoJSON(ST_UNION(ways.the_geom)) FROM pgr_dijkstra('{sql}', %s, %s, directed := false) LEFT JOIN ways ON (edge = gid);",
                (start_id, end_id))
    geojson = cur.fetchone()[0]

    return flask.Response(status=200, response=geojson, mimetype='application/json')


# command line ---------------------------------------------------------------


def cli():
    """Run Parasol on localhost with Flask built-in server"""
    ap = argparse.ArgumentParser(
        description='Parasol Navigation - MVP Edition',
        formatter_class= argparse.ArgumentDefaultsHelpFormatter)
    ap.add_argument('--debug', action='store_true',
        help='run server in "debug mode"')
    ap.add_argument('--host', type=str, default='0.0.0.0',
        help='hostname for flask server')
    ap.add_argument('--port', type=int, default=5000,
        help='server port number')
    args = ap.parse_args()

    app.run(host=args.host, port=args.port, debug=args.debug)
