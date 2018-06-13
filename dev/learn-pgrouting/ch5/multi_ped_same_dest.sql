SELECT * FROM pgr_dijkstra(
    'SELECT gid AS id,
         source,
         target,
         length_m AS cost
        FROM ways',
    ARRAY[5291, 10247], 10916,
    directed := false);
