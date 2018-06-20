# Parasol: Shade model and routing algorithm for comfortable travel outdoors 

# Contents

+ **pitch**: Idea pitch materials
+ **dev**: Various development scripts
+ **mvp**: Minimal Viable Program 
+ **release**: Final version for release

## Notes for later

+ Have to set a special env variable to enable GTiff output from Postgres. See
  https://postgis.net/docs/postgis_installation.html . Add the following to
  /etc/postgresql/10/main/enviroment: `POSTGIS_GDAL_ENABLED_DRIVERS=ENABLE_ALL`
