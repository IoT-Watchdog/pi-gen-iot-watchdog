#!/bin/bash

# Update pi-gen
cd externals/pi-gen
git checkout -- stage2/EXPORT_NOOBS
git checkout -- stage2/02-net-tweaks/00-packages
git pull

# Don't build the NOOBS Image
rm stage2/EXPORT_NOOBS

# Don't install dhcpcd5, use network-manager
sed -i "s|raspberrypi-net-mods||"   stage2/02-net-tweaks/00-packages
sed -i "s|dhcpcd5|network-manager|" stage2/02-net-tweaks/00-packages
