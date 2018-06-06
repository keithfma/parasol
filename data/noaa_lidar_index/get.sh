#!/bin/bash

mkdir -p dist
mkdir -p data
cd dist
wget https://coast.noaa.gov/htdata/lidar1_z/geoid12b/data/4914/tileindex.zip
unzip tileindex.zip -d ../data
