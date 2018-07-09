#!/bin/bash

gunzip -c dist/laszip-src-3.2.2.tar.gz | tar xvf -
mv laszip-src-3.2.2 src
mkdir build
cd build
cmake -DCMAKE_BUILD_TYPE=release ../src
make
sudo make install
ldconfig -n -v /usr/local/lib
