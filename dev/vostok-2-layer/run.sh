#!/bin/bash
set -x
pdal pipeline prep.json
pdal pipeline shade.json
pdal pipeline grnd.json
set +x
