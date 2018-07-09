#!/bin/bash
# Install parasol dependencies using apt -- tested with fresh Ubuntu 18.04 LTS installation
# Run as root.
# #

# install packages
sudo apt -y install postgresql postgresql-client-common python3-pip unzip cmake-curses-gui \
	postgresql-server-dev-10 libxml2-dev libcunit1-dev autoconf postgresql-10-postgis-2.4 \
	postgresql-10-pgrouting

# build and install additional dependencies
cd deps/laszip
./install.sh

cd ../pgpointcloud
./install.sh
