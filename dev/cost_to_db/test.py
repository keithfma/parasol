"""Scratch space for getting cost into columns in OSM database"""

import parasol
import pickle 
import json

with open('/home/keith/.parasol/osm/ways_pts.pkl', 'rb') as fp:
    wpts = pickle.load(fp)
 
parasol.osm.update_cost_db(wpts)

