#!/bin/bash
# Format VOSTOK output so it can be read by PDAL
# #

cat "X,Y,Z,NormalX,NormalY,NormalZ,Solar" > output.csv
cat output.xyz >> output.csv
