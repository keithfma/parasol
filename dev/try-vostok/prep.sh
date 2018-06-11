#!/bin/bash
# Post-process PDAL output to prepare for VOSTOK
# #

pdal pipeline prep-vostok.json
tail -n +2 prepared.csv > prepared.xyz
sed -i 's/,/ /g' prepared.xyz
