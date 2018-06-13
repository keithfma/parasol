#!/bin/bash
# run all processing steps -- this is slow so it may make sense to
#   comment/uncomment and run a step at a time
# #

# echo "START PREP"
# pdal pipeline prep.json
# echo "END PREP"
# 
# echo "START SHADE"
# pdal pipeline shade.json &
# shade_pid=$!
# 
# echo "START GRND"
# pdal pipeline grnd.json &
# grnd_pid=$!
# 
# wait $shade_pid
# tail -n +2 shade.csv > shade.xyz
# sed -i 's/,/ /g' shade.xyz
# 
# wait $grnd_pid
# tail -n +2 grnd.csv > grnd.xyz
# sed -i 's/,/ /g' grnd.xyz
# echo "END SHADE & GRND"

voxel_size=1.0
latitude=42.31854518
longitude=-71.275732405
year=2018
day=150
minute=0
time_zone=-5
output_file='output.xyz'

for hour in $(seq 6 4 18); do
    echo "VOSTOK HOUR = $hour"
    printf -v tif_name "output_%02dh.tif" $hour
    vostok-instant shade.xyz grnd.xyz $output_file --voxel $voxel_size \
        --lat $latitude --lon $longitude --year $year --day $day --hour $hour \
        --min $minute --tz $time_zone 
    pdal pipeline --nostream output.json
    mv output.tif $tif_name
done
