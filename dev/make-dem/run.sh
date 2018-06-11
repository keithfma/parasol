#!/bin/bash

IN_FILE=./in.laz
OUT_FILE=./out.laz

pdal pipeline pipeline.json --readers.las.filename=$IN_FILE --writers.las.filename=$OUT_FILE
