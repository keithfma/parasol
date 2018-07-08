"""
Create two plots: one of classified lidar points, and the other of the
resulting surfaces
"""

import parasol
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import numpy as np
import scipy.interpolate
from scipy.spatial import cKDTree


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


# # plot surfaces --------------------------------------------------------------
# 
# sx, sy, sz = parasol.surface.retrieve(XMIN, XMAX, YMIN, YMAX, 'surface')
# gx, gy, gz = parasol.surface.retrieve(XMIN, XMAX, YMIN, YMAX, 'ground')
# 
# vmin, vmax = np.percentile(sz, [0, 95])
# 
# fig_a = plt.figure()
# plt.imshow(sz, extent=(XMIN, XMAX, YMIN, YMAX), vmin=vmin, vmax=vmax)
# plt.xticks([])
# plt.yticks([])
# plt.savefig('surface.png', bbox_inches='tight')
# 
# fig_b = plt.figure()
# plt.imshow(gz, extent=(XMIN, XMAX, YMIN, YMAX), vmin=vmin, vmax=vmax)
# plt.xticks([])
# plt.yticks([])
# plt.savefig('ground.png', bbox_inches='tight')
# 
# 
# # plot lidar ----------------------------------------------------------------
# 
# pts = parasol.lidar.retrieve(XMIN, XMAX, YMIN, YMAX)
# 
# xmin = min(pts[:,0])
# xmax = max(pts[:,0])
# ymin = min(pts[:,1])
# ymax = max(pts[:,1])
# 
# fig = plt.figure()
# ax = plt.axes(projection='3d')
# ax.scatter3D(pts[::QUAL, 0], pts[::QUAL, 1], pts[::QUAL, 2],
#     c=pts[::QUAL, 2],
#     marker='.', 
#     s=1,
#     cmap='viridis',
#     depthshade=False, 
#     vmax=vmax, 
#     vmin=vmin)
# ax.view_init(50, -135)
# ax.set_xticks([])
# ax.set_xlim([xmin, xmax])
# ax.set_yticks([])
# ax.set_ylim([ymin, ymax])
# ax.set_zticks([])
# ax.grid(False)
# ax.set_frame_on(False)
# 
# plt.savefig('lidar.png', dpi=600, bbox_inches='tight')


# plot filter explationation -------------------------------------------------

# extract a thin swatch from the point data
swath_x = sx[0, 150:153]
swath_x_min = min(swath_x)
swath_x_max = max(swath_x)
swath_y = sy[300:, 0]
swath_y_min = min(swath_y)
swath_y_max = max(swath_y)
swath_mask = np.logical_and(
    np.logical_and(pts[:,0] >= swath_x_min, pts[:,0] <= swath_x_max),
    np.logical_and(pts[:,1] >= swath_y_min, pts[:,1] <= swath_y_max)
    )
swath = pts[swath_mask, :]

# label points as surface or ground
surf_mask = np.logical_and(np.logical_or(swath[:,3] == 1, swath[:,4] == 1), swath[:,5] == 1)
surf_yz = swath[surf_mask,1:3]
surf_yz = surf_yz[np.argsort(surf_yz[:,0]), :]

grnd_mask = np.logical_and(swath[:,3] == swath[:,4], swath[:,5] == 2)
grnd_yz = swath[grnd_mask,1:3]
grnd_yz = grnd_yz[np.argsort(grnd_yz[:,0]), :]

# other_mask = ~np.logical_or(surf_mask, grnd_mask)
# other_yz = swath[other_mask,1:3]

# plot the points
plt.scatter(surf_yz[:,0], surf_yz[:,1], marker='o', facecolor='none', edgecolor='blue', label='surface')
plt.scatter(grnd_yz[:,0], grnd_yz[:,1], marker='o', facecolor='none', edgecolor='green', label='ground')
# plt.scatter(other_yz[:,0], other_yz[:,1], marker='x', facecolor='none', edgecolor='red')
plt.legend()
plt.show()

# # interpolate surface (no need, just plot line)
# surf_interp = scipy.interpolate.interp1d(surf_yz[:,0], surf_yz[:,1], kind='slinear', assume_sorted=False)
# yi = np.linspace(min(surf_yz[:,0]), max(surf_yz[:,0]), 1000)
# zi = surf_interp(yi)
# plt.plot(yi, zi)

# plot with linear interpolation
plt.scatter(surf_yz[:,0], surf_yz[:,1], marker='o', facecolor='none', edgecolor='blue', label='surface')
plt.scatter(grnd_yz[:,0], grnd_yz[:,1], marker='o', facecolor='none', edgecolor='green', label='ground')
plt.plot(surf_yz[:,0], surf_yz[:,1], color='blue', label='surface-interpolated')
plt.plot(grnd_yz[:,0], grnd_yz[:,1], color='green', label='ground-interpolated')
plt.legend()
plt.show()

# TODO: plot with NN average filter
surf_tree = cKDTree(surf_yz[:,0]) 
#     xy_grd = np.hstack([x_grd.reshape((-1,1)), y_grd.reshape((-1,1))])
#     nn_dist, nn_idx = tree.query(xy_grd, k=16)
# 
#     # compute local medians
#     z_grds.append(np.median(zz[nn_idx], axis=1).reshape(x_grd.shape))
# 
# 
# # TODO: plot with NN median filter
# 
