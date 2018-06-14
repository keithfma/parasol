"""
Flask server for Parasol API/UI
"""

import flask
import argparse
import os
from pkg_resources import resource_filename


# constants

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
    filename = resource_filename('parasol_mvp', os.path.join('static', 'img', img_name))
    return flask.send_file(filename, mimetype='image/png')


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
