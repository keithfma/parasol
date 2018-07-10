#!/bin/bash

# unpack binaries
rm -rf build
unzip dist/geoserver-2.13.1-bin.zip
mv geoserver-2.13.1 build 
 
# install!
install_dir=/usr/share/geoserver
sudo cp -r build $install_dir
 
# # configure to run as daemon with non-privledged user
user=geoserver
sudo adduser --system $user
sudo addgroup $user
sudo usermod -a -G $user $user
sudo chgrp -R $user $install_dir
sudo chmod -R g+w $install_dir

# create systemd unit file
cat << EOF | sudo tee /etc/systemd/system/geoserver.service > /dev/null
[Unit]
Description=GeoServer
After=network.target

[Service]
User=$user
Environment=JAVA_HOME=/usr/lib/jvm/java-8-openjdk-amd64
Environment=JRE_HOME=/usr/lib/jvm/java-8-openjdk-amd64/jre
Environment=GEOSERVER_HOME=$install_dir
ExecStart=$install_dir/bin/startup.sh
ExecStop=$install_dir/bin/shutdown.sh

[Install]
WantedBy=multi-user.target
EOF

# enable and start service
sudo systemctl enable geoserver.service
sudo systemctl start geoserver.service
