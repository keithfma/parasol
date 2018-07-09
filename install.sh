#!/bin/bash
# Install parasol dependencies using apt -- tested with fresh Ubuntu 18.04 LTS installation
# Run as root.
# #

# install system packages
sudo apt -y install postgresql postgresql-client-common python3-pip unzip cmake-curses-gui \
	postgresql-server-dev-10 libxml2-dev libcunit1-dev autoconf postgresql-10-postgis-2.4 \
	postgresql-10-pgrouting gdal-bin libgdal-dev 

# install python packages
# note: most dependencies are install in setup.py, but building PDAL requires a few be pre-installed
sudo pip3 install numpy
sudo pip3 install cython
sudo pip3 install packaging

# build and install additional dependencies
cd deps/laszip
./install.sh

cd ../pgpointcloud
./install.sh

cd ../pdal
./install.sh
