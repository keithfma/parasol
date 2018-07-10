# GeoServer

SOURCE: http://sourceforge.net/projects/geoserver/files/GeoServer/2.13.1/geoserver-2.13.1-bin.zip

Using pre-built binaries (Java, system independent)

Requires Java 8. I modified the startup / shutdown scripts to set JAVA_HOME,
etc so that they point to the correct version.

Also requres a GEOSERVER_HOME env variable, likewise inserted into these
scripts.

Also added the "Image Mosaic JDBC" extension: http://docs.geoserver.org/stable/en/user/data/raster/imagemosaicjdbc.html

