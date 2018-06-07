#!/bin/bash

mkdir -p dist
mkdir -p data
cd dist
wget http://files.hubwaydatachallenge.org/hubway-updated-26-feb-2014.zip
unzip hubway-updated-26-feb-2014.zip -d ../data
