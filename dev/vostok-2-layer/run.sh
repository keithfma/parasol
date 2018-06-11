#!/bin/bash
set -x

# # prepare vostok input files
# pdal pipeline prep.json
# 
# pdal pipeline shade.json
# tail -n +2 shade.csv > shade.xyz
# sed -i 's/,/ /g' shade.xyz
# 
# pdal pipeline grnd.json
# tail -n +2 grnd.csv > grnd.xyz
# sed -i 's/,/ /g' grnd.xyz

# run VOSTOK
vostok output.sol

# create grid
pdal pipeline --nostream output.json

set +x
