"""Quick test script for pgpointcloud data management"""

import parasol
import logging

logging.basicConfig(level=logging.INFO)

# # # ingest tiny dataset, save results to viewable file
# # parasol.lidar.create_db(True)
# # sample_file = 'subset.laz'
# maxx = 315118.39                                                                                                                                                                                
# minx = 315000                                                                                                                                                                                   
# maxy = 4686154.02                                                                                                                                                                               
# miny = 4686000                                                                                                                                                                                
# # parasol.lidar.ingest(sample_file)
# # pts = parasol.lidar.retrieve(minx, maxx, miny, maxy)
# 
# # experiment with gridding
# top = parasol.lidar.grid_points(minx, maxx, miny, maxy, grnd=False)
# bot = parasol.lidar.grid_points(minx, maxx, miny, maxy, grnd=True)

# try full tile
# parasol.lidar.create_db(True)
# tile_file = 'tile.laz'
maxx = 335999.6937      
maxy = 4696499.905      
minx = 334499.6937
miny = 4694999.905       
# parasol.lidar.ingest(tile_file)
top = parasol.lidar.grid_points(minx, maxx, miny, maxy, grnd=False)
bot = parasol.lidar.grid_points(minx, maxx, miny, maxy, grnd=True)


