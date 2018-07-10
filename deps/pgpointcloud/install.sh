#!/bin/bash

gunzip -c dist/v1.1.1.tar.gz | tar xvf -
mv pointcloud-1.1.1 src
cd src
./autogen.sh 
./configure
make
sudo make install
