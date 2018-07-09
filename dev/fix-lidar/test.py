"""
Figure out a way to fix the surface gridding routines - they are terribly slow and broken now
"""

from parasol import common, cfg
import shapely

xmin = 327480.17
xmax = 328500.17
ymin = 4689458.81
ymax = 4690478.81

with common.connect_db(cfg.LIDAR_DB) as conn, conn.cursor() as cur:
    cur.execute(f'SELECT PC_AsText(pa) FROM lidar WHERE PC_Intersects(pa, ST_MakeEnvelope({xmin}, {ymin}, {xmax}, {ymax}, {cfg.PRJ_SRID})) LIMIT 100')
    pas = [json.loads(x[0])['pts'] for x in cur] 

# NOTE: it looks like I am calling the retrieve function wrong! the printed
#   bounds are not in the expected order, so the domain is huge
