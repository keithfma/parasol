"""
Subroutines shared across multiple modules
"""

import math


def tile_limits(x_min, x_max, y_min, y_max, x_tile, y_tile):
    """
    Return list of bounding boxes for tiles within the specified range
    
    Arguments:
        x_min, x_max, y_min, y_max: floats, limits for the full region-of-interest
        x_tile, y_tile: floats, desired dimensions for generated tiles, note that
            the actual dimensions are adjusted to evenly divide the ROI
    
    Returns: list of bounding boxes, each a dict with fields x_min, x_max, y_min, y_max
    """
    # modify the bounding box to be a multiple of the tile dimension
    x_pad = (x_max - x_min) % x_tile
    x_min += math.ceil(x_pad/2)
    x_max += math.floor(x_pad/2) 
    x_num_tiles = int((x_max - x_min) // x_tile)

    y_pad = (y_max - y_min) % y_tile
    y_min += math.ceil(y_pad/2)
    y_max += math.floor(y_pad/2) 
    y_num_tiles = int((y_max - y_min) // y_tile)

    # generate tile bboxes
    tiles = []
    for ii in range(x_num_tiles):
        for jj in range(y_num_tiles):
            tile = {}
            tile['x_min'] = x_min + ii*x_tile
            tile['x_max'] = tile['x_min'] + x_tile
            tile['y_min'] = y_min + jj*y_tile
            tile['y_max'] = tile['y_min'] + y_tile
            tiles.append(tile)

    return tiles
