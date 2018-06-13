SELECT *
FROM pgr_dijkstraCost(
    'SELECT gid AS id,
         source,
         target,
         length_m  / 1.3 / 60 AS cost
        FROM ways',
    ARRAY[5291, 10247], ARRAY[10916, 12345],
    directed := false);
