"""Quick test script for pgpointcloud data management"""

import parasol

# create empty DB
parasol.lidar.create_db(True)

# ingest tiny dataset, save results to viewable file
sample_file = 'subset.laz'
maxx = 315118.39                                                                                                                                                                                
minx = 315000                                                                                                                                                                                   
maxy = 4686154.02                                                                                                                                                                               
miny = 4686000                                                                                                                                                                                

parasol.lidar.ingest(sample_file)
pts = parasol.lidar.retrieve(minx, maxx, miny, maxy, 'result.laz')


