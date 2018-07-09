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

[3] Download the original LiDAR data by running the `download.sh` script in
the `data/noaa_lidar` folder. This script reads off the URLs from the file
`url_list.txt`. If you want to change the domain, you will need to modify this
file to list the correct data sources.

[4] Install the `parasol` package using `pip`. Keep track of where it is
installed to, so that you can modify the config file to match your
installation. This step installs a suite of command line scripts that you will
use in the next step.

[5] Make a local copy of the config file in the installation directory (`cp
config.json.default config.json`). Note that this will be done automatically
the first time your import the package, if you do not do it manually. Then,
edit the various values in the file to reflect your local configuration (e.g.,
PSQL user, etc). See the table below for a description of each config parameter.

TODO: Document config parameters in a table

[6] Run all the first-time setup scripts installed with `parasol`. Each has a
`--help` options which you should consult for usage details. Run the scripts in
the order shown below, though your command line options may vary from this
example.
```shell
parasol-init-lidar
parasol-init-surface
parasol-init-shade # beware! this step needs a lot of memory (not yet using tiles)
```

## Notes for later

+ installing wxpython: https://uwpce-pythoncert.github.io/Py300/notes/Installing_wxPython.html
+ https://wxpython.org/pages/downloads/
+ https://stackoverflow.com/questions/720806/wxpython-for-python-3
