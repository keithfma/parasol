"""
Exploratory code for creating and populating the raster database
"""

import parasol
import logging

logging.basicConfig(level=logging.INFO)

parasol.raster.create_db(clobber=True)

