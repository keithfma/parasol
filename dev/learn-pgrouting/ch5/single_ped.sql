SELECT * FROM pgr_dijkstra(
    'SELECT gid AS id,
         source,
         target,
         length AS cost
        FROM ways',
    5291, 10247,
    directed := false);
