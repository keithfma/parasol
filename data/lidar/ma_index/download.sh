#!/bin/bash
# Download this data source
# #

mkdir -p dist
wget http://download.massgis.digital.mass.gov/shapefiles/state/lidarindex_poly.zip
mv lidarindex_poly.zip dist
