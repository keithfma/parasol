"""Scratch script for developing cost plot"""

import parasol
import pickle

# constants
way_file = '/home/keith/.parasol/osm/ways.pkl'
way_pts_file = '/home/keith/.parasol/osm/ways_pts.pkl'
hour = 9
minute = 10

# # load data
# with open(way_file, 'rb') as fp:
#     ways = pickle.load(fp)
# with open(way_pts_file, 'rb') as fp:
#     way_pts = pickle.load(fp)

# compute insolation along ways at some time
way_pts_sol, ways_sol = parasol.osm.way_insolation(hour, minute, way_pts)

parasol.osm.plot_way_insolation_pts(way_pts, way_pts_sol, vmin=100, vmax=1000, downsample=1, show=True)

