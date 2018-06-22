"""Test work on retrieving points from LiDAR db direct"""

import parasol

x_min = 327516
x_max = x_min + 10 
y_min = 4692153
y_max = y_min + 10

out = parasol.lidar.retrieve_db(x_min, x_max, y_min, y_max)

