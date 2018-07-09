"""
Figure out a way to fix the surface gridding routines - they are terribly slow and broken now
"""

from parasol import common, cfg
import shapely
import uuid
import json
import numpy as np

xmin = 327480.17
xmax = 328500.17
ymin = 4689458.81
ymax = 4690478.81

# fetch_chunk = 1000
# point_chunk = fetch_chunk*cfg.LIDAR_CHIP
# 
# # using a named cursor to avoid bulk data transfer
# cur_name = uuid.uuid4().hex
# with common.connect_db(cfg.LIDAR_DB) as conn, conn.cursor(cur_name) as cur:
#     cur.execute(f'SELECT PC_AsText(pa) FROM lidar WHERE PC_Intersects(pa, ST_MakeEnvelope({xmin}, {ymin}, {xmax}, {ymax}, {cfg.PRJ_SRID})) LIMIT 100')
#     data = []
#     while True:
#         chunk = []
#         for rec in cur.fetchmany(fetch_chunk):
#             chunk.extend(json.loads(rec[0])['pts'])
#         data.append(chunk)

with common.connect_db(cfg.LIDAR_DB) as conn, conn.cursor() as cur:
    cur.execute(f'SELECT PC_AsText(PC_Union(pa)) FROM lidar WHERE PC_Intersects(pa, ST_MakeEnvelope({xmin}, {ymin}, {xmax}, {ymax}, {cfg.PRJ_SRID}))')
    data = np.array( json.loads(cur.fetchone()[0])['pts'] )
