"""Scratch space for route metadata calculation"""

import parasol
import numpy as np
from datetime import datetime

lat0=42.3671571
lon0=-71.0631095
lat1=42.35184265
lon1=-71.0550228973888
betas=np.arange(0, 1, 0.05)
time = datetime.now().replace(hour=9, minute=15, second=0, microsecond=0)

# shortest
print('SHORTEST')
meters, sun, geojson = parasol.routing.route_shortest(lon0, lat0, lon1, lat1, time)
print(f'length={meters:.2f}, sun={sun:.2f}')

# optimal(s)
print('OPTIMALS')
for beta in betas:
    meters, sun, geojson = parasol.routing.route_optimal(lon0, lat0, lon1, lat1, time, beta)
    print(f'beta={beta:.2f}, length={meters:.2f}, sun={sun:.2f}')
