#!/bin/bash
# Run once to initalize the routing postgresql database
#  See: https://workshop.pgrouting.org/2.4.11/en/index.html
# #

# NOTE: user creation / access config has to be done manually

DBNAME=parasol_mvp
OSMFILE=~/.parasol_mvp/osm/all.osm

# create / init database
createdb $DBNAME
psql -d $DBNAME -a << SQL
CREATE EXTENSION postgis;
CREATE EXTENSION pgrouting;
SQL

# ingest data (assumes it it downloaded)
osm2pgrouting -f $OSMFILE -d $DBNAME  --clean
