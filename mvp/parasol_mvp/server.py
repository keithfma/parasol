"""
Flask server for Parasol API/UI
"""

import flask
import argparse
import os
from pkg_resources import resource_filename
import psycopg2


# constants
PSQL_DB = 'parasol_mvp'
PSQL_USER = 'keith'

# create app
app = flask.Flask('parasol_mvp')


# endpoints ------------------------------------------------------------------


@app.route('/', methods=["GET"])
@app.route('/ui', methods=["GET"])
def main():
    """Main Parasol user interface"""
    return flask.render_template('index.html')


@app.route('/img/<img_name>', methods=['GET'])
def img_file(img_name):
    """Serve files in static/img by name"""
    filename = resource_filename('parasol_mvp', os.path.join('static', 'img', img_name))
    return flask.send_file(filename, mimetype='image/png')


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
    conn = psycopg2.connect(f"dbname={PSQL_DB} user={PSQL_USER}")
    cur = conn.cursor()

    # find start vertex
    cur.execute("SELECT id FROM ways_vertices_pgr ORDER BY the_geom <-> ST_SetSRID(ST_Point(%s, %s), 4326) LIMIT 1;",
                (lon0, lat0))
    start_id = cur.fetchone()[0]

    # find end vertex
    cur.execute("SELECT id FROM ways_vertices_pgr ORDER BY the_geom <-> ST_SetSRID(ST_Point(%s, %s), 4326) LIMIT 1;",
                (lon1, lat1))
    end_id = cur.fetchone()[0]
    
    # DEBUG
    print(start_id, end_id)

    return flask.Response(status=501)


# command line ---------------------------------------------------------------


def cli():
    """Run Parasol on localhost with Flask built-in server"""
    ap = argparse.ArgumentParser(
        description='Parasol Navigation - MVP Edition',
        formatter_class= argparse.ArgumentDefaultsHelpFormatter)
    ap.add_argument('--debug', action='store_true',
        help='run server in "debug mode"')
    ap.add_argument('--port', type=int, default=5000,
        help='server port number')
    args = ap.parse_args()

    app.run(port=args.port, debug=args.debug)
