#!/bin/bash
# Post-process PDAL output to prepare for VOSTOK
# #

tail -n +2 prepared.csv > prepared.xyz
sed -i 's/,/ /g' prepared.xyz
