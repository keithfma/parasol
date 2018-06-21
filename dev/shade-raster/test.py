"""Explore generating and ingesting shade rasters"""

import parasol
import logging


logging.basicConfig(level=logging.INFO)


# # extract a subset and write out as geotiff -----------------
x_min = 334499.6937
x_max = 335000
y_min = 4694999.905       
y_max = 4695500
# parasol.raster.retrieve_geotiff('delete_me', x_min, x_max, y_min, y_max)

# test the automated version ---------------------------------

# parasol.shade.geotiff_to_layer('delete_me_surface.tif', 'surface')
# parasol.shade.layers_to_geotiff('.')

parasol.shade.insolation(x_min, x_max, y_min, y_max, 2018, 150)



# NOTES: some notes from manually generating shade layers in GRASS --------------------------

# g.region raster=delete_me_surface@parasol-scratch 
# r.slope.aspect --overwrite elevation=delete_me_surface@parasol-scratch slope=slope aspect=aspect
# r.latlong input=delete_me_surface@parasol-scratch output=lat              
# r.latlong -l input=delete_me_surface@parasol-scratch output=lon                 
# r.sun.hourly  elevation=delete_me_surface@parasol-scratch aspect=aspect@parasol-scratch slope=slope@parasol-scratch start_time=12 end_time=13 time_step=0.5 day=150 year=2018 glob_rad_basename=radiation

# import os
# import subprocess
# 
# os.environ['GISBASE'] = '/usr/lib/grass74'
# os.environ['GISRC'] = '/home/keith/.grass7/rc'
# 
# for tt in range(0, 2401, 25):
#     num_str = '{:04d}'.format(tt)
#     time_str = num_str[0:2] + '.' + num_str[2:]
#     layer_name = f'top_rad_{time_str}@mvp'
#     file_name = f'/home/keith/.parasol_mvp/lidar/rad/rad_{time_str}.tif'
#     subprocess.run(['grass74', '/home/keith/.grassdata/parasol-dev/mvp', '--exec', 'r.out.gdal', f'input={layer_name}', f'output={file_name}', 'format=GTiff'])

# # show matching raster and vector maps but do not delete yet (as verification)
# g.remove type=raster,vector pattern="tmp_*"
# 
# # actually delete the matching raster and vector maps
# g.remove -f type=raster,vector pattern="tmp_*"
