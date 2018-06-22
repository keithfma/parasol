#!/bin/bash
# Run once to initalize the routing postgresql database
#  See: https://workshop.pgrouting.org/2.4.11/en/index.html
# #

# NOTE: user creation / access config has to be done manually

DBNAME=parasol-osm
OSMFILE=~/prj/parasol/repo/data/osm/dist/all.osm

# create / init database
createdb $DBNAME
psql -U $1 -P $2 -d $DBNAME -a << SQL
CREATE EXTENSION postgis;
CREATE EXTENSION pgrouting;
SQL

# ingest data (assumes it it downloaded)
osm2pgrouting -U $1 -W $2 -f $OSMFILE -d $DBNAME  --clean
