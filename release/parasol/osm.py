"""
OpenStreetMap data handlers
"""

import os
import pyproj
import logging
import wget

from parasol import DATA_DIR, GEO_SRID, PRJ_SRID, DOMAIN_XLIM, DOMAIN_YLIM


logger = logging.getLogger(__name__)


# constants
OSM_DIR = os.path.join(DATA_DIR, 'osm')
OSM_FILE = os.path.join(OSM_DIR, 'domain.osm')


def fetch_data():
    """
    Download OpenStreetMaps data for the Parasol study area
    """
    # get OSM bounding box (geographic)
    prj0 = pyproj.Proj(init=f'epsg:{PRJ_SRID}')
    prj1 = pyproj.Proj(init=f'epsg:{GEO_SRID}')
    ll = pyproj.transform(prj0, prj1, DOMAIN_XLIM[0], DOMAIN_YLIM[0])
    lr = pyproj.transform(prj0, prj1, DOMAIN_XLIM[1], DOMAIN_YLIM[0])
    ul = pyproj.transform(prj0, prj1, DOMAIN_XLIM[0], DOMAIN_YLIM[1])
    ur = pyproj.transform(prj0, prj1, DOMAIN_XLIM[1], DOMAIN_YLIM[1])
    lons = [ll[0], lr[0], ur[0], ul[0]]
    lats = [ll[1], lr[1], ur[1], ul[1]]
    
    print(lons, lats)

    # create output folder if needed
    if not os.path.isdir(OSM_DIR):
        logger.info(f'Created directory {OSM_DIR}')
        os.makedirs(OSM_DIR)

    # fetch data from OSM overpass API
    # ...cribbed example from: https://github.com/pgRouting/osm2pgrouting/issues/44
    bbox_str = f'{min(lons)},{min(lats)},{max(lons)},{max(lats)}'
    url = f'http://www.overpass-api.de/api/xapi?*[bbox={bbox_str}][@meta]'
    logger.info(f'Downloading OSM data from: {url}')
    wget.download(url, out=OSM_FILE)
