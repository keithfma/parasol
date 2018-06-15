"""Development for routing endpoint"""

import psycopg2

PSQL_DB = 'parasol_mvp'
PSQL_USER = 'keith'

conn = psycopg2.connect(f"dbname={PSQL_DB} user={PSQL_USER}")
cur = conn.cursor()

# find nearest vertex
cur.execute("SELECT id FROM ways_vertices_pgr ORDER BY the_geom <-> ST_SetSRID(ST_Point(%s, %s), 4326) LIMIT 1;",
            (-71.04143, 42.35126))
start_id = cur.fetchone()[0]

cur.execute("SELECT id FROM ways_vertices_pgr ORDER BY the_geom <-> ST_SetSRID(ST_Point(%s, %s), 4326) LIMIT 1;",
            (-71.06143, 42.35126))
end_id = cur.fetchone()[0]

# compute route
sql ='SELECT gid AS id, source, target, length AS cost FROM ways'
cur.execute(f"SELECT * FROM pgr_dijkstra('{sql}', %s, %s, directed := false);",
            #(4847, 9270))
            (start_id, end_id))
route = cur.fetchall()


# compute route, return GeoJSON for edges
sql ='SELECT gid AS id, source, target, length AS cost, the_geom FROM ways'
cur.execute(f"SELECT ST_AsGeoJSON(ST_UNION(ways.the_geom)) FROM pgr_dijkstra('{sql}', %s, %s, directed := false) LEFT JOIN ways ON (edge = gid);",
            (start_id, end_id))
route_geojson = cur.fetchone()[0]
