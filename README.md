# Parasol: Shade model and routing algorithm for comfortable travel outdoors 

## Contents

+ **pkg**: Final version for release
+ **data**: Supporting datasets 
+ **dev**: Various development scripts
+ **deps**: Various dependencies that must be built/installed manually
+ **install.sh**: Install dependencies (Ubuntu Linux only)

## Getting Started

There are quite a few dependencies, and some require a bit of manual
configuration. I have tried to automate where practical, and to document the
remaining steps. That said, be warned: this is not an easy package to get up
and running.

[1] Run the `install.sh` script, which takes care of installing many of the
dependencies.

[2] Configure a postgresql user. Run the following lines, replacing 'USER'
with your preferred postgresql user name. You will be prompted to set up a
password.  The username and password should go in your parasol config file.
```shell
sudo -i -u postgres
createuser --createdb --createrole --pwprompt --superuser USER 
```

[3] Annoyingly, GRASS GIS appears to require an interactive first-time setup
(prove me wrong, please!). Open the GRASS GUI from the command line (`grass`),
and create a new database and location. The names and coordinate systems must
match the values in your `config.json` (see below), so make sure they do.

[4] Change the default password for your geoserver user. Go to
`http://<your-ip-here>:8080/geoserver` and login with the default username
`admin` and password `geoserver`. Navigate to the "Users, Groups, Roles"
section, and update your password. Keep the new password handy to add to the
parasol config file (see below).

[5] Install the `parasol` package using `pip`. Keep track of where it is
installed to, so that you can modify the config file to match your
installation. This step installs a suite of command line scripts that you will
use in the next step.

[6] Make a local copy of the config file in the installation directory (`cp
config.json.default config.json`). Note that this will be done automatically
the first time your import the package, if you do not do it manually. Then,
edit the various values in the file to reflect your local configuration (e.g.,
PSQL user, etc). See the table below for a description of each config parameter.

TODO: Document config parameters in a table

[7] Run all the first-time setup scripts installed with `parasol`. Each has a
`--help` options which you should consult for usage details. Run the scripts in
the order shown below, though your command line options may vary from this
example.
```shell
parasol-init-lidar
parasol-init-surface
parasol-init-shade
parasol-update-shade
parasol-init-geoserver
parasol-init-osm
parasol-update-osm
```
Note that the two `parsol-update-*` functions can be called again to update the
shade rasters and costs for the current day.

## Run Parasol application with Flask development server

It's easy! Just run the command line script `parasol-server`. Add the `--help`
flag to see the various available options.

## Setup and run deployed application with Apache and mod\_wsgi

TODO
