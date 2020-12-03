#!/bin/bash -e

cd /opt/ctraspion
export DEBIAN_FRONTEND=noninteractive

echo "* Hilfspakete hinzufügen, Paketlisten aktualisieren"
dpkg -i debs/raspion-keyring_2019_all.deb
dpkg -i debs/apt-ntop_1.0.190416-469_all.deb

echo "* Pakete vorkonfigurieren ..."
sudo debconf-set-selections debconf/wireshark
sudo debconf-set-selections debconf/iptables-persistent

echo "* Raspbian aktualisieren ..."
apt-get -y -q --allow-downgrades dist-upgrade

echo "* Pakete installieren ..."
apt-get install -y -q --allow-downgrades --no-install-recommends wireshark-gtk libgtk-3-bin ntopng iptables-persistent
cat > /etc/ntopng/ntopng.conf <<EOF
--community
--disable-login 1
--http-port 3000
--interface wlan0
--dump-flows "mysql;localhost;ntopng;flows-%Y.%m.%d;root;jKD7ubqVeg"
EOF

chown redis:redis /var/lib/redis/dump.rdb
chmod 660 /var/lib/redis/dump.rdb

# See also:
# http://variwiki.com/index.php?title=Wifi_NetworkManager#Configuring_WiFi_Access_Point
cat > /etc/NetworkManager/system-connections/Accesspoint <<EOF
[connection]
id=Accesspoint
uuid=d18b82ec-40c3-44a7-8864-f134f162e1a1
type=wifi
interface-name=wlan0

[wifi]
band=bg
channel=1
mode=ap
ssid=IoT-Watchdog

[wifi-security]
group=ccmp;
key-mgmt=wpa-psk
pairwise=ccmp;
proto=rsn;
psk=Netidee2019

[ipv4]
address1=192.168.42.1/24
method=shared

[ipv6]
addr-gen-mode=stable-privacy
method=auto
EOF

chmod 600 /etc/NetworkManager/system-connections/Accesspoint

systemctl enable broadwayd
systemctl enable wireshark

sudo usermod -a -G wireshark pi
sudo usermod -a -G www-data pi

mkdir -p /home/pi/.config/wireshark
cp files/recent /home/pi/.config/wireshark
cp files/preferences_wireshark /home/pi/.config/wireshark/preferences
cp files/settings.ini /etc/gtk-3.0

chown pi:pi /home/pi -R

rm -r /opt/ctraspion

