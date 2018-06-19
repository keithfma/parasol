"""
Explore generating padded tiles within a bounding box
"""

from matplotlib import pyplot as plt
import json

# define outer bounding box (from config file)
with open('../../release/parasol/config.json', 'r') as fp:
    bbox = json.load(fp)['BBOX_PRJ'] 


# plot outer bounding box
plt.plot([bbox[0][0], bbox[0][1], bbox[0][1], bbox[0][0], bbox[0][0]],
         [bbox[1][0], bbox[1][0], bbox[1][1], bbox[1][1], bbox[1][0]])


# define tile dimensions
tile_dim = [500, 500]

# modify tile dimensions to a nice multiple of the bounding box
x_bbox_rng = bbox[0][1] - bbox[0][0]
x_num_tiles = x_bbox_rng // tile_dim[0]
tile_dim[0] = x_bbox_rng / x_num_tiles 

y_bbox_rng = bbox[1][1] - bbox[1][0]
y_num_tiles = y_bbox_rng // tile_dim[1]
tile_dim[1] = y_bbox_rng / y_num_tiles 

# generate tile bboxes, and plot
bbox_tiles = []
for ii in range(x_num_tiles):
    for jj in range(y_num_tiles):
        x0 = bbox[0][0] + ii*tile_dim[0]
        x1 = x0 + tile_dim[0]
        y0 = bbox[1][0] + jj*tile_dim[1]
        y1 = y0 + tile_dim[1]
        bbox_tiles.append([[x0, x1], [y0, y1]])
        plt.plot([x0, x1, x1, x0, x0], [y0, y0, y1, y1, y0],
                 linestyle=":", color='r')

# add padding to tile bboxes
# --> trivial, don't bother doing this here

# show plot
plt.gca().set_aspect('equal', 'box')
plt.show()


