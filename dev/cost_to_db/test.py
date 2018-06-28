"""Scratch space for getting cost into columns in OSM database"""

import parasol
import pickle 
import json

with open('/home/keith/.parasol/osm/ways_pts.pkl', 'rb') as fp:
    wpts = pickle.load(fp)
 
sql, params = parasol.osm.update_cost_db(wpts)

# recs = {}
# for ii, kk in enumerate(cost):
#     if ii % 1000 == 0:
#         sub[kk] = cost[kk]
# 
# sub_json = json.dumps(sub)



