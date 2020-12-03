#!/bin/bash -e

# Delete password for default user
# passwd --delete pi

# Delete default user
#deluser --remove-home pi

# Set password for default user
echo "${FIRST_USER_NAME}:iot-watch.1415" | chpasswd

# Set Timezone Vienna
rm /etc/localtime
ln -s /usr/share/zoneinfo/Europe/Vienna /etc/localtime
dpkg-reconfigure -f noninteractive tzdata

chmod 600 /root/.ssh/id_rsa-raspies
sed -i -e 's/AcceptEnv/AcceptEnv EDITOR GIT_COMMITTER_* GIT_AUTHOR_*/' /etc/ssh/sshd_config

# Services
## Speed up Boot time
systemctl disable alsa-restore.service
systemctl disable rsyslog.service
systemctl disable nfs-config.service

## Specific for our usecase
systemctl disable dnsmasq.service
systemctl disable hostapd.service
systemctl enable bt-agent.service
systemctl enable nap.service
systemctl enable systemd-networkd.service

systemctl enable cpustats.service
systemctl enable dbusage.service
systemctl enable iostats2mqtt.service
systemctl enable vcgencmd-stats.service

systemctl enable reset_ntopng.service

mkdir -p /etc/networkd-dispatcher/routable.d/
mkdir -p /etc/networkd-dispatcher/off.d/
ln -f -s /usr/local/bin/wireless-status-mqtt.py /etc/networkd-dispatcher/routable.d/wireless-status-mqtt.py
ln -f -s /usr/local/bin/wireless-status-mqtt.py /etc/networkd-dispatcher/off.d/wireless-status-mqtt.py

# TODO: Find out if we want this
systemctl disable systemd-networkd-wait-online.service

# sed -i 's/exit 0/\/bin\/hciconfig hci0 piscan\nexit 0/' /etc/rc.local
sed -i -e 's/^#\s*DiscoverableTimeout = 0/DiscoverableTimeout = 0/' /etc/bluetooth/main.conf
