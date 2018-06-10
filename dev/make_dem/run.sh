#!/bin/bash

IN_FILE=/home/keith/prj/parasol/repo/data/noaa_lidar_sandy/dist/20131208_usgspostsandy_19TCG120875.laz
OUT_FILE=./out

pdal pipeline pipeline.json --readers.las.filename=$IN_FILE --writers.las.filename=$OUT_FILE.las
