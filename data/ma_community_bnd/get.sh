#!/bin/bash

mkdir -p dist
mkdir -p data
cd dist 
wget http://download.massgis.digital.mass.gov/shapefiles/state/townssurvey_shp.zip
cd ..
unzip dist/townssurvey_shp.zip -d data
