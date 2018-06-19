"""
Compute reduced bounds from current bbox

Current values are for tile: ../../data/noaa_lidar/dist/20131208_usgspostsandy_19TCG150860.laz
"""

bbox = {
    "maxx": -71.2263106,
    "maxy": 42.3181271,
    "maxz": 411.5147994,
    "minx": -71.244972,
    "miny": 42.3042767,
    "minz": -11.91378045
    }

frac = 0.10

rngx = bbox['maxx'] - bbox['minx']
xlim = [bbox['minx'], bbox['minx'] + frac*rngx]

rngy = bbox['maxy'] - bbox['miny']
ylim = [bbox['miny'], bbox['miny'] + frac*rngy]

print((xlim, ylim))
