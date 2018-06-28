from parasol import cfg, common


def route(lon0, lat0, lon1, lat1):
    """
    Compute route between specified start and end points

    Parameters (URL query string):
        lat0, lon0 = floats, start point latitude, longitude
        lat1, lon1 = floats, end point latitude, longitude

    Returns: optimal route as geoJSON
    """
    with common.connect_db(cfg.OSM_DB) as conn, conn.cursor() as cur:
    
        # find start/end vertices
        cur.execute("SELECT id FROM ways_vertices_pgr ORDER BY the_geom <-> ST_SetSRID(ST_Point(%s, %s), 4326) LIMIT 1;",
                    (lon0, lat0))
        start_id = cur.fetchone()[0]
        cur.execute("SELECT id FROM ways_vertices_pgr ORDER BY the_geom <-> ST_SetSRID(ST_Point(%s, %s), 4326) LIMIT 1;",
                    (lon1, lat1))
        end_id = cur.fetchone()[0]

        # compute route, return GeoJSON for edges
        sql ='SELECT gid AS id, source, target, length AS cost, the_geom FROM ways'
        cur.execute(f"SELECT ST_AsGeoJSON(ST_UNION(ways.the_geom)) FROM pgr_dijkstra('{sql}', %s, %s, directed := false) LEFT JOIN ways ON (edge = gid);",
                    (start_id, end_id))
        geojson = cur.fetchone()[0]

    return geojson
