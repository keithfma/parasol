from parasol import cfg, common
import numpy as np
import math
from datetime import datetime, timedelta
from pdb import set_trace
from osgeo import ogr, osr
import logging


logger = logging.getLogger(__name__)


def _route(lon0, lat0, lon1, lat1, time=None, beta=None):
    """
    Shared utility to retrieve route from pgrouting server
    
    Arguments: 
        lat0, lon0 = floats, start point latitude, longitude
        lat1, lon1 = floats, end point latitude, longitude
        time: 
        beta: 
    
    Returns: meters, sun, geojson
        meters: total length of route in meters
        sun: total solar cost (normalized units)
        geojson: optimal route as geoJSON
    """
    # parse time
    if time is None:
        time = datetime.now()
    if not isinstance(time, datetime):
        raise TypeError('Argument "time" must be a datetime object')

    # get cost columns corresponding to current date/time
    delta = timedelta(hours=9999) # arbitrarily large
    # TODO: use common.shade_meta()
    for fhours in np.arange(cfg.SHADE_START_HOUR, cfg.SHADE_STOP_HOUR, cfg.SHADE_INTERVAL_HOUR):
        this_hour = math.floor(fhours)
        this_minute = math.floor((fhours - this_hour)*60)
        this_time = datetime.now().replace(hour=this_hour, minute=this_minute, second=0, microsecond=0)
        this_delta = abs(time - this_time)
        if this_delta <= delta:
            sun_cost = f'{cfg.OSM_SUN_COST_PREFIX}{this_time.hour:02d}{this_time.minute:02d}'
            shade_cost = f'{cfg.OSM_SHADE_COST_PREFIX}{this_time.hour:02d}{this_time.minute:02d}'
            delta = this_delta

    # sql expression for cost (shortest or optimal)
    if beta is None:
        # shortest
        cost_expr = 'length_m'
    elif beta >= 0 and beta <= 1:
        # optimal
        cost_expr = f'{1 - beta} * {sun_cost} + {beta} * {shade_cost}'
    else:
        # invalid
        raise ValueError('"beta" must be either in the range [0, 1] or None')
    
    # find start/end vertices
    start_id = nearest_id(lon0, lat0)
    end_id = nearest_id(lon1, lat1)

    # compute djikstra path, return total length, total sun cost, and route
    with common.connect_db(cfg.OSM_DB) as conn, conn.cursor() as cur:
        inner_sql = f'SELECT gid AS id, source, target, {cost_expr} AS cost, the_geom FROM ways'
        cur.execute(f"SELECT SUM(length_m), SUM({sun_cost}), ST_AsGeoJSON(ST_Union(the_geom)) "
                    f"FROM pgr_dijkstra('{inner_sql}', {start_id}, {end_id}, directed := false) "
                    f"LEFT JOIN ways ON (edge = gid);")
        return cur.fetchone()


def route_shortest(lon0, lat0, lon1, lat1, time):
    """
    Compute shortest route between specified start and end points

    Parameters (URL query string):
        lat0, lon0 = floats, start point latitude, longitude
        lat1, lon1 = floats, end point latitude, longitude
        time: datetime at which to calculate the path, for this function the
            path is unaffected, but the solar cost returned will change

    Returns: meters, sun, geojson
        meters: total length of route in meters
        sun: total solar cost (normalized units)
        geojson: optimal route as geoJSON
    """
    return _route(lon0, lat0, lon1, lat1, time, beta=None)


def route_optimal(lon0, lat0, lon1, lat1, time, beta):
    """
    Compute optimal (wrt sun/shade) route between specified start and end points

    Parameters (URL query string):
        lat0, lon0 = floats, start point latitude, longitude
        lat1, lon1 = floats, end point latitude, longitude
        time: datetime at which to calculate the path, for this function the
            path and solar cost are affected
        beta: float, sun/shade preference parameter

    Returns: meters, sun, geojson
        meters: total length of route in meters
        sun: total solar cost (normalized units)
        geojson: optimal route as geoJSON
    """
    return _route(lon0, lat0, lon1, lat1, time, beta)


def nearest_id(lon, lat):
    """
    Return record ID for nearest vertex in the OSM database
    
    Arguments:
        lon, lat: floats, longitude and latitude (WGS84) of the query point

    Returns: int, record ID for nearest point
    """
    with common.connect_db(cfg.OSM_DB) as conn, conn.cursor() as cur:
        cur.execute("SELECT id FROM ways_vertices_pgr ORDER BY the_geom <-> ST_SetSRID(ST_Point(%s, %s), 4326) LIMIT 1;",
                    (lon, lat))
        return cur.fetchone()[0]
    

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

    
