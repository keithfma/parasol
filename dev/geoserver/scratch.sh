#!/bin/bash

# https://gis.stackexchange.com/questions/6479/programming-geoserver-2-0-2-to-add-a-raster-data-store-and-layer-without-the-ui


# curl -u admin:geoserver http://localhost:8080/geoserver/rest/workspaces/delete_me/coveragestores/test

# curl -u admin:geoserver -v -XPOST -H 'Content-type: text/xml' \
#      -d '<workspace><name>wsgeotiff</name></workspace>' \
#      http://localhost:8080/geoserver/rest/workspaces
# 
# curl -u admin:geoserver -v -XPOST -H 'Content-type: text/xml' \
#      -d '<coverageStore>
#          <name>wsgeotiff_imageGeoTiffWGS84_1298678792699</name>
#          <workspace>wsgeotiff</workspace>
#          <enabled>true</enabled>
#          <type>GeoTIFF</type>
#          <data_dir>/home/keith/prj/parasol/repo</data_dir>
#          <url>/dev/geoserver/sol_09:00.tif</url>
#          </coverageStore>' \
#      "http://localhost:8080/geoserver/rest/workspaces/wsgeotiff/coveragestores?configure=all"
# 
# curl -u admin:geoserver -v -XPOST -H 'Content-type: text/xml' \
#       -d '<coverage>
#           <name>imageGeoTiffWGS84</name>
#           <title>imageGeoTiffWGS84</title>
#           <nativeCRS>GEOGCS[&quot;WGS 84&quot;,DATUM[&quot;World Geodetic System 1984&quot;,SPHEROID[&quot;WGS 84&quot;,6378137.0, 298.257223563, AUTHORITY[&quot;EPSG&quot;,&quot;7030&quot;]],AUTHORITY[&quot;EPSG&quot;,&quot;6326&quot;]],PRIMEM[&quot;Greenwich&quot;, 0.0, AUTHORITY[&quot;EPSG&quot;,&quot;8901&quot;]],UNIT[&quot;degree&quot;, 0.017453292519943295],AXIS[&quot;Geodetic longitude&quot;, EAST],AXIS[&quot;Geodetic latitude&quot;, NORTH],AUTHORITY[&quot;EPSG&quot;,&quot;4326&quot;]]</nativeCRS>
#           <srs>EPSG:4326</srs>
#           <latLonBoundingBox><minx>-179.958</minx><maxx>-105.002</maxx><miny>-65.007</miny><maxy>65.007</maxy><crs>EPSG:4326</crs></latLonBoundingBox>
#           </coverage>' \
#       "http://localhost:8080/geoserver/rest/workspaces/wsgeotiff/coveragestores/wsgeotiff_imageGeoTiffWGS84_1298678792699/coverages"

# WORKED: create one, then use GET calls to retrieve the right syntax for making more

# {"coverageStore":{"name":"test_2","description":"Random raster for testing","type":"GeoTIFF","enabled":true,"workspace":{"name":"delete_me","href":"http:\/\/localhost:8080\/geoserver\/rest\/workspaces\/delete_me.json"},"_default":false,"url":"file:\/\/\/home\/keith\/prj\/parasol\/repo\/dev\/shade-raster\/sol_10.00.tif","coverages":"http:\/\/localhost:8080\/geoserver\/rest\/workspaces\/delete_me\/coveragestores\/test\/coverages.json"}}

# curl -i -u admin:geoserver -XPOST -H 'Content-type: application/json' -d '@test.json' http://localhost:8080/geoserver/rest/workspaces/delete_me/coveragestores


# curl -u admin:geoserver -XGET http://localhost:8080/geoserver/rest/workspaces/delete_me/coveragestores/test_2/coverages/sol_10.00.json 

#  {"coverage":{"name":"sol_10.00","nativeName":"sol_10.00","namespace":{"name":"delete_me","href":"http:\/\/localhost:8080\/geoserver\/rest\/namespaces\/delete_me.json"},"title":"sol_10.00","description":"Generated from GeoTIFF","keywords":{"string":["sol_10.00","WCS","GeoTIFF"]},"nativeCRS":{"@class":"projected","$":"PROJCS[\"WGS 84 \/ UTM zone 19N\", \n  GEOGCS[\"WGS 84\", \n    DATUM[\"World Geodetic System 1984\", \n      SPHEROID[\"WGS 84\", 6378137.0, 298.257223563, AUTHORITY[\"EPSG\",\"7030\"]], \n      AUTHORITY[\"EPSG\",\"6326\"]], \n    PRIMEM[\"Greenwich\", 0.0, AUTHORITY[\"EPSG\",\"8901\"]], \n    UNIT[\"degree\", 0.017453292519943295], \n    AXIS[\"Geodetic longitude\", EAST], \n    AXIS[\"Geodetic latitude\", NORTH], \n    AUTHORITY[\"EPSG\",\"4326\"]], \n  PROJECTION[\"Transverse_Mercator\", AUTHORITY[\"EPSG\",\"9807\"]], \n  PARAMETER[\"central_meridian\", -69.0], \n  PARAMETER[\"latitude_of_origin\", 0.0], \n  PARAMETER[\"scale_factor\", 0.9996], \n  PARAMETER[\"false_easting\", 500000.0], \n  PARAMETER[\"false_northing\", 0.0], \n  UNIT[\"m\", 1.0], \n  AXIS[\"Easting\", EAST], \n  AXIS[\"Northing\", NORTH], \n  AUTHORITY[\"EPSG\",\"32619\"]]"},"srs":"EPSG:32619","nativeBoundingBox":{"minx":334499,"maxx":335000,"miny":4695003,"maxy":4695500,"crs":{"@class":"projected","$":"EPSG:32619"}},"latLonBoundingBox":{"minx":-71.01079813172157,"maxx":-71.004572315837,"miny":42.38969274359408,"maxy":42.39427256975878,"crs":"EPSG:4326"},"projectionPolicy":"REPROJECT_TO_DECLARED","enabled":true,"metadata":{"entry":{"@key":"dirName","$":"test_2_sol_10.00"}},"store":{"@class":"coverageStore","name":"delete_me:test_2","href":"http:\/\/localhost:8080\/geoserver\/rest\/workspaces\/delete_me\/coveragestores\/test_2.json"},"nativeFormat":"GeoTIFF","grid":{"@dimension":"2","range":{"low":"0 0","high":"501 497"},"transform":{"scaleX":1,"scaleY":-1,"shearX":0,"shearY":0,"translateX":334499.5,"translateY":4695499.5},"crs":"EPSG:32619"},"supportedFormats":{"string":["ImageMosaic","Gtopo30","GIF","PNG","JPEG","TIFF","GEOTIFF","ImageMosaicJDBC","ArcGrid","GeoPackage (mosaic)"]},"interpolationMethods":{"string":["nearest neighbor","bilinear","bicubic"]},"defaultInterpolationMethod":"nearest neighbor","dimensions":{"coverageDimension":[{"name":"GRAY_INDEX","description":"GridSampleDimension[-Infinity,Infinity]","range":{"min":"-inf","max":"inf"},"dimensionType":{"name":"REAL_32BITS"}}]},"requestSRS":{"string":["EPSG:32619"]},"responseSRS":{"string":["EPSG:32619"]},"parameters":{"entry":[{"string":"InputTransparentColor","null":""},{"string":["SUGGESTED_TILE_SIZE","512,512"]}]},"nativeCoverageName":"sol_10.00"}}




curl -v -u admin:geoserver -XPOST -H "Content-type: text/xml" -d "<style><name>roads_style</name><filename>roads.sld</filename></style>" http://localhost:8080/geoserver/rest/styles
