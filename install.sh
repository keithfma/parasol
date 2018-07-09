#!/bin/bash
# Install parasol dependencies using apt -- tested with fresh Ubuntu 18.04 LTS installation
# Run as root.
# #

# install packages
sudo apt -y install postgresql postgresql-client-common python3-pip unzip cmake-curses-gui

# build and install additional dependencies
cd deps/laszip
./install.sh
