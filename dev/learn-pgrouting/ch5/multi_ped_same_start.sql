SELECT * FROM pgr_dijkstra(
    'SELECT gid AS id,
         source,
         target,
         length_m AS cost
        FROM ways',
    10916, ARRAY[5291, 10247], 
    directed := false);
