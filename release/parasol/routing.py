from parasol import cfg, common
import numpy as np
import math
from datetime import datetime, timedelta
from pdb import set_trace
from osgeo import ogr, osr


def route(lon0, lat0, lon1, lat1, beta):
    """
    Compute route between specified start and end points

    Parameters (URL query string):
        lat0, lon0 = floats, start point latitude, longitude
        lat1, lon1 = floats, end point latitude, longitude
        beta: float, sun/shade preference parameter

    Returns: optimal route as geoJSON
    """
    # get column corresponding to current date/time
    now = datetime.now()
    delta = timedelta(hours=999)
    solar_cost_col = None
    for fhours in np.arange(cfg.SHADE_START_HOUR, cfg.SHADE_STOP_HOUR, cfg.SHADE_INTERVAL_HOUR):
        hour = math.floor(fhours)
        minute = math.floor((fhours-hour)*60)
        this_time = datetime.now().replace(hour=hour, minute=minute, second=0, microsecond=0)
        this_name = f'{cfg.OSM_SOLAR_COST_PREFIX}{hour:02d}{minute:02d}'
        this_delta = abs(now - this_time)
        if this_delta <= delta:
            solar_cost_col = this_name
            delta = this_delta 
    
    # compute optimal route
    with common.connect_db(cfg.OSM_DB) as conn, conn.cursor() as cur:
    
        # find start/end vertices
        cur.execute("SELECT id FROM ways_vertices_pgr ORDER BY the_geom <-> ST_SetSRID(ST_Point(%s, %s), 4326) LIMIT 1;",
                    (lon0, lat0))
        start_id = cur.fetchone()[0]
        cur.execute("SELECT id FROM ways_vertices_pgr ORDER BY the_geom <-> ST_SetSRID(ST_Point(%s, %s), 4326) LIMIT 1;",
                    (lon1, lat1))
        end_id = cur.fetchone()[0]

        # compute route, return GeoJSON for edges
        sql = f'SELECT gid AS id, source, target, length_m * 1000 + {beta}*{solar_cost_col} AS cost, the_geom FROM ways'
        cur.execute(f"SELECT ST_AsGeoJSON(ST_UNION(ways.the_geom)) FROM pgr_dijkstra('{sql}', %s, %s, directed := false) LEFT JOIN ways ON (edge = gid);",
                    (start_id, end_id))
        geojson = cur.fetchone()[0]

    return geojson


def route_length(lon0, lat0, lon1, lat1, beta):
    """
    Compute length of input route - used for optimizing beta parameter

    Arguments:
        lat0, lon0 = floats, start point latitude, longitude
        lat1, lon1 = floats, end point latitude, longitude
        beta: float, sun/shade preference parameter

    Returns: optimal route length in meters
    """
    # get route as geojson
    rt_json = route(lon0, lat0, lon1, lat1, beta)

    # get coordinate transform to cartesian
    prj0 = osr.SpatialReference()
    prj0.ImportFromEPSG(4326) # WGS84, default coord sys for OSM
    prj1 = osr.SpatialReference()
    prj1.ImportFromEPSG(cfg.PRJ_SRID)
    transform = osr.CoordinateTransformation(prj0, prj1)
    
    # load and transform route
    rt_obj = ogr.CreateGeometryFromJson(rt_json)
    rt_obj.Transform(transform)

    return rt_obj.Length()


def plot_beta(lon0, lat0, lon1, lat1):
    # start with a simple grid to get some intuition, later, might want a real optimizer
    # betas np.arange(0.5, 1.5, :79
    pass

    
