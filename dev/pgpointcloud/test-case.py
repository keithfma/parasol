"""Quick test script for pgpointcloud data management"""

import parasol

# create empty DB
parasol.lidar.create_db(True)

# ingest tiny dataset, save results to viewable file
sample_file = 'subset.laz'
parasol.lidar.ingest(sample_file)
parasol.lidar.retrieve(-71.244972, -71.24310586, 42.3042767, 42.305661740000005, 'result.laz')

