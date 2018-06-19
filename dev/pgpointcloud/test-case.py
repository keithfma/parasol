"""Quick test script for pgpointcloud data management"""

import parasol
import logging

logging.basicConfig(level=logging.INFO)

# ingest tiny dataset, save results to viewable file
parasol.lidar.create_db(True)
sample_file = 'subset.laz'
maxx = 315118.39                                                                                                                                                                                
minx = 315000                                                                                                                                                                                   
maxy = 4686154.02                                                                                                                                                                               
miny = 4686000                                                                                                                                                                                
parasol.lidar.retrieve(minx, maxx, miny, maxy, sample_file)
# pts = parasol.lidar.retrieve(minx, maxx, miny, maxy, sample_file)



