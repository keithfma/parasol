"""
Figure out a way to fix the surface gridding routines - they are terribly slow and broken now
"""

from parasol import common, cfg, lidar
import shapely
import uuid
import json
import numpy as np

xmin = 327480.17
xmax = 328500.17
ymin = 4689458.81
ymax = 4690478.81

with common.connect_db(cfg.LIDAR_DB) as conn, conn.cursor() as cur:
    cur.execute(f'SELECT PC_AsText(PC_Union(pa)) FROM lidar WHERE PC_Intersects(pa, ST_MakeEnvelope({xmin}, {ymin}, {xmax}, {ymax}, {cfg.PRJ_SRID}))')
    data = np.array(json.loads(cur.fetchone()[0])['pts']) # ordered as ReturnNumber,NumberOfReturns,Classification,X,Y,Z
    data = np.roll(data, 3) # ordered as X,Y,Z,ReturnNumber,NumberOfReturns,Classification

data2 = lidar.retrieve(xmin, xmax, ymin, ymax)

