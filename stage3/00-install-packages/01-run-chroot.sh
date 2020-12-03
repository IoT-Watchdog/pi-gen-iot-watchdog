#!/bin/bash

apt-key add /influxdb.key
echo "deb https://repos.influxdata.com/debian buster stable" > /etc/apt/sources.list.d/influxdb.list
apt-get update
rm /influxdb.key

apt install -y /root/debs/*deb
