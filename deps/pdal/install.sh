#!/bin/bash

gunzip -c dist/PDAL-1.7.2-src.tar.gz | tar -xvf -
mv PDAL-1.7.2-src src
mkdir build
cd build
cmake -DBUILD_PLUGIN_PYTHON=ON -DCMAKE_BUILD_TYPE=release ../src
make
sudo make install
ldconfig -n -v /usr/local/lib

