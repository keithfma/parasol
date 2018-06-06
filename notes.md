+ Some "award-winning" LiDAR processing tools: https://github.com/LAStools/LAStools

+ Should I use the existing tools entirely? Should I use them for
  pre-processing only (i.e., scanline correction)? Is there some advantage to my
  alpha-shape idea? Is there some advantage to my voxel + morphological filtering
  idea?

+ Not sure if the "overlap" points between flight paths are a problem for me or
  not. If the problem is just density, then I don't care, but if there is a
  vertical offset, I will have to deal with it. Some useful discussion at:
  https://gis.stackexchange.com/questions/270961/open-source-approach-to-classifying-and-removing-lidar-points-from-overlapping-s

+ Progressive Morphological Filtering (PMF) provides a nice way to separate
  ground from vegetation points. The reference is Zhang et al 2003. There is a
  Python implementation in the PDAL library: https://pdal.io/
