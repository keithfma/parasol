"""Scratch space for route metadata calculation"""

import parasol
import numpy as np

lat0=42.3671571
lon0=-71.0631095
lat1=42.35184265
lon1=-71.0550228973888
betas=np.arange(0, 1, 0.05)
hour=9
minute=0


for beta in betas:
    meters, sun, geojson = parasol.routing.route(lon0, lat0, lon1, lat1, beta, hour, minute)
    print(f'beta={beta:.2f}, length={meters:.2f}, sun={sun:.2f}')
