#!/bin/bash
# Install parasol dependencies using apt -- tested with fresh Ubuntu 18.04 LTS installation
# Run as root.
# #

# install system packages
sudo apt -y install postgresql postgresql-client-common python3-pip unzip cmake-curses-gui \
	postgresql-server-dev-10 libxml2-dev libcunit1-dev autoconf postgresql-10-postgis-2.4 \
	postgresql-10-pgrouting gdal-bin libgdal-dev python3-gdal python3-tk grass-dev \
	python-gdal x11-apps grass-gui openjdk-8-jre

# retrieve missing proj4 datum files
mkdir vdatum
cd vdatum
dest_dir=/usr/share/proj
wget http://download.osgeo.org/proj/vdatum/usa_geoid2012.zip && sudo unzip -j -u usa_geoid2012.zip -d $dest_dir 
wget http://download.osgeo.org/proj/vdatum/usa_geoid2009.zip && sudo unzip -j -u usa_geoid2009.zip -d $dest_dir 
wget http://download.osgeo.org/proj/vdatum/usa_geoid2003.zip && sudo unzip -j -u usa_geoid2003.zip -d $dest_dir 
wget http://download.osgeo.org/proj/vdatum/usa_geoid1999.zip && sudo unzip -j -u usa_geoid1999.zip -d $dest_dir 
wget http://download.osgeo.org/proj/vdatum/vertcon/vertconc.gtx && sudo mv vertconc.gtx $dest_dir 
wget http://download.osgeo.org/proj/vdatum/vertcon/vertcone.gtx && sudo mv vertcone.gtx $dest_dir 
wget http://download.osgeo.org/proj/vdatum/vertcon/vertconw.gtx && sudo mv vertconw.gtx $dest_dir 
wget http://download.osgeo.org/proj/vdatum/egm96_15/egm96_15.gtx && sudo mv egm96_15.gtx $dest_dir
wget http://download.osgeo.org/proj/vdatum/egm08_25/egm08_25.gtx && sudo mv egm08_25.gtx $dest_dir
cd ..
rm -rf vdatum

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

cd ../geoserver
./install.sh
