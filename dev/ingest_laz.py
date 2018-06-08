"""
Development script exploring ingesting LAZ files into a database
"""

import pdal
import json

input_file = '/home/keith/prj/parasol/repo/data/noaa_lidar_sandy/dist/20131208_usgspostsandy_19TCG120875.laz'
pipeline_json = json.dumps({
    "pipeline": [
        input_file,
        ]
    })
pipeline = pdal.Pipeline(pipeline_json)
pipeline.validate() # check if our JSON and options were good
pipeline.loglevel = 8 #really noisy
count = pipeline.execute()
arrays = pipeline.arrays
metadata = pipeline.metadata
log = pipeline.log

