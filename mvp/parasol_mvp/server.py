"""
Flask server for Parasol API/UI
"""

import flask
import argparse


app = flask.Flask('parasol_mvp')


@app.route('/', methods=["GET"])
@app.route('/ui', methods=["GET"])
def main():
    """Main Parasol user interface"""
    return flask.render_template('index.html')


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
