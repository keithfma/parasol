"""
Retrieve rad rasters from the Grass database -- this should not be so hard
"""

import os
import subprocess

os.environ['GISBASE'] = '/usr/lib/grass74'
os.environ['GISRC'] = '/home/keith/.grass7/rc'

for tt in range(0, 2401, 25):
    time_str = str(tt)[0:2] + '.' + str(tt)[2:]
    layer_name = f'top_rad_{time_str}@mvp'
    file_name = f'/home/keith/.parasol-mvp/lidar/rad/rad_{time_str}.tif'
    subprocess.run(['grass74', '/home/keith/.grassdata/parasol-dev/mvp', '--exec', 'r.out.gdal', f'input={layer_name}', f'output={file_name}', 'format=GTiff'])

