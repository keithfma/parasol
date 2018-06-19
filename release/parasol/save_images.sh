#!/bin/bash
# Generate PNGs from original rad files
# #

src_dir=~/.parasol/lidar/rad
dst_dir=~/prj/parasol/repo/mvp/parasol/static/img
tmp_file=delete_me.tif
min_rad=0
max_rad=1050

for src_file in $src_dir/*.tif ; do
    base=`basename $src_file`
    time_str=${base:4:5}
    dst_file=$dst_dir/shade_$time_str.png
    rm $tmp_file
    gdalwarp -s_srs EPSG:32619 $src_file -t_srs EPSG:4326 -of GTiff $tmp_file
    gdal_translate -scale $rad_min $rad_max -of PNG $tmp_file $dst_file
done

