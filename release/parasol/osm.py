"""
OpenStreetMap data handlers
"""

import pyproj
from parasol import GEO_SRID, DOMAIN_XLIM, DOMAIN_YLIM


def fetch_data():
    """
    Download OpenStreetMaps data for the Parasol study area
    """
    # get OSM bounding box (geographic)
    prj0 = pyproj.Proj(init=f'epsg:{GEO_SRID}')
    prj1 = pyproj.Proj(init=f'epsg:{PRJ_SRID}')
    ll = prj.transform()
    x1,y1 = -11705274.6374,4826473.6922
    x2,y2 = transform(inProj,outProj,x1,y1)
    print x2,y2

    # # create output folder if needed
    # if not os.path.isdir(PARASOL_OSM):
    #     logger.info(f'Created directory {PARASOL_OSM}')
    #     os.makedirs(PARASOL_OSM)

    # # fetch data from OSM overpass API
    # # ...cribbed example from: https://github.com/pgRouting/osm2pgrouting/issues/44
    # file_name = os.path.join(PARASOL_OSM, 'all.osm')
    # bbox_str = '{lon_min},{lat_min},{lon_max},{lat_max}'.format(**bbox)
    # url = f'http://www.overpass-api.de/api/xapi?*[bbox={bbox_str}][@meta]'
    # logger.info(f'Downloading OSM data from: {url}')
    # wget.download(url, out=file_name)
