#!/bin/bash
set -x
pdal pipeline prep.json –verbose=Info 
pdal pipeline shade.json
pdal pipeline grnd.json
set +x
