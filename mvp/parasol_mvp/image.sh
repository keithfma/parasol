#!/bin/bash

src_file=~/.parasol_mvp/lidar/merge/top_merge.tif
tmp_file=delete_me.tif
dest_file=top.png

gdalwarp -s_srs EPSG:32619 $src_file -t_srs EPSG:4326 -of GTiff $tmp_file
gdal_translate -scale -of PNG $tmp_file $dest_file
