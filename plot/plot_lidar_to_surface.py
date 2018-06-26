"""
Create two plots: one of classified lidar points, and the other of the
resulting surfaces
"""

import parasol
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import numpy as np


# constants ------------------------------------------------------------------


# XMIN = 331000.000
# XMAX = 331500.000
# YMIN = 4691000.000
# YMAX = 4691500.000
XMIN = 329000.000
XMAX = 329500.000
YMIN = 4691000.000
YMAX = 4691500.000
QUAL = 50 


# plot surfaces --------------------------------------------------------------


sx, sy, sz = parasol.surface.retrieve(XMIN, XMAX, YMIN, YMAX, 'surface')
gx, gy, gz = parasol.surface.retrieve(XMIN, XMAX, YMIN, YMAX, 'ground')

vmin, vmax = np.percentile(sz, [0, 95])

fig_a = plt.figure()
plt.imshow(sz, extent=(XMIN, XMAX, YMIN, YMAX), vmin=vmin, vmax=vmax)
plt.title('Upper Surface Elevation')
plt.xticks([XMIN, XMAX])
plt.yticks([YMIN, YMAX])
plt.savefig('surface.png', bbox_inches='tight')

fig_b = plt.figure()
plt.imshow(gz, extent=(XMIN, XMAX, YMIN, YMAX), vmin=vmin, vmax=vmax)
plt.title('Ground Surface Elevation')
plt.xticks([XMIN, XMAX])
plt.yticks([YMIN, YMAX])
plt.savefig('ground.png', bbox_inches='tight')


# plot lidar ----------------------------------------------------------------


pts = parasol.lidar.retrieve(XMIN, XMAX, YMIN, YMAX)

pts[:,0] = pts[:,0] - min(pts[:,0])
pts[:,1] = pts[:,1] - min(pts[:,1])
xmin = min(pts[:,0])
xmax = max(pts[:,0])
ymin = min(pts[:,1])
ymax = max(pts[:,1])

fig = plt.figure()
ax = plt.axes(projection='3d')
ax.scatter3D(pts[::QUAL, 0], pts[::QUAL, 1], pts[::QUAL, 2],
    c=pts[::QUAL, 2],
    marker='.', 
    s=1,
    cmap='viridis',
    depthshade=False, 
    vmax=vmax, 
    vmin=vmin)
ax.view_init(50, -135)
ax.set_xticks([xmin, xmax])
ax.set_xlim([xmin, xmax])
ax.set_yticks([ymin, ymax])
ax.set_ylim([ymin, ymax])
ax.set_zticks([])
ax.grid(False)
ax.set_frame_on(False)

plt.savefig('lidar.png', dpi=600, bbox_inches='tight')



