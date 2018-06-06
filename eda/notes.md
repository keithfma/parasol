# Exploratory Data Analysis

+ For the study area, I'd like a manageable dataset that includes urban and
  suburban areas. I used the MA LiDAR index shapefile and a town boundary
  shapefile to figure out which LiDAR dataset to get. If my study area is Boston,
  Cambridge, Somerville, Brookline, Arlington, Belmont, Newton, then the "Sandy"
  LiDAR survey is sufficient.

+ A quick look at the LiDAR-derived DEM suggests it is not useful for me. The
  interpolation is full of artefacts, and there is no ability to pick out
  trees.  Looks like we will have to do this the hard way.
