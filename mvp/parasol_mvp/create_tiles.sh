#!/bin/bash

src_file=~/.parasol_mvp/lidar/merge/top_merge.tif
tmp_file_1=top_1.tif
tmp_file_2=top_2.tif
dest_folder=tiles

rm $tmp_file_1 $tmp_file_2
gdalwarp -s_srs EPSG:32619 $src_file -t_srs EPSG:3857 -of GTiff $tmp_file_1
gdal_translate -of GTiff -scale $tmp_file_1 $tmp_file_2
gdal2tiles.py -p mercator -z 10-16 -w leaflet $tmp_file_2 $dest_folder


