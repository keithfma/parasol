## QGIS

gdal_merge.py -n -9999 -a_nodata -9999 /home/keith/.parasol_mvp/lidar/top_dem/20131208_usgspostsandy_19TCG285890_top.tif /home/keith/.parasol_mvp/lidar/top_dem/20131208_usgspostsandy_19TCG285905_top.tif /home/keith/.parasol_mvp/lidar/top_dem/20140407_usgspostsandy_19TCG300890_top.tif /home/keith/.parasol_mvp/lidar/top_dem/20140407_usgspostsandy_19TCG300905_top.tif

gdal_merge.py -n -9999 -a_nodata -9999 -of GTiff -o /home/keith/.parasol_mvp/lidar/merge/bottom_merge /home/keith/.parasol_mvp/lidar/bottom_dem/20131208_usgspostsandy_19TCG285890_bottom.tif /home/keith/.parasol_mvp/lidar/bottom_dem/20131208_usgspostsandy_19TCG285905_bottom.tif /home/keith/.parasol_mvp/lidar/bottom_dem/20140407_usgspostsandy_19TCG300890_bottom.tif /home/keith/.parasol_mvp/lidar/bottom_dem/20140407_usgspostsandy_19TCG300905_bottom.tif


## GRASS

r.null map=top_merge@mvp null=0

