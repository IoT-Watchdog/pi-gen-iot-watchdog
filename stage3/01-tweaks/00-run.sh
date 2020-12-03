#!/bin/bash -e

rm -f "${ROOTFS_DIR}/etc/systemd/system/dhcpcd.service.d/wait.conf"

# Enable ssh
touch ${ROOTFS_DIR}/boot/ssh

# Authorized Keys
mkdir -p ${ROOTFS_DIR}/root/.ssh
cat > ${ROOTFS_DIR}/root/.ssh/authorized_keys <<EOF
ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAACAQDHS9HCn125v+cw+77dtseP/BwTjiR+Wp1nYiLnvhdF5rrHRIiOn+Eiuqz40FVhtPXI5vLYGOM0CpEx5uturhqwblhtBavBqgUyyk4TZy5PcNO1rmMJiI80f2I+Y8tFK0jF/lx3CK7mHCkwTuLDhSafOrrM9VSOaNs9Ihk4tlWckxyxE9vSTuXrk4McyWehLN9nRZVFjdaPfdL8qV78FI/RML9oH7TmElBeQJvX0cbvuSrZj1PzEla/azX28Wg9dKeWwgFK1niwz1tYgsibMqjHSebBERZ164SbxkP3Erts4BBxrSUQNabYydKW79m3ee0IsWzMYMFCu8YAtQHxXzxxaE76zofJFANywmvuDbg+z/9yPK8B8WaCa5xUfZQ9dk0o5gHuyDoLz+0LAW9V4LGZzR87jZU/R5SCethiHfzaznbRl2p1Iih3tUhJPI1dJ5RoSYH03hBKSIyoBfsRWwh1DyWGVknLa0Qj0aFs61Zv7tnQU5QFn+7KEcDC2aL96T1KUrMDn0JVJ0vlTlyCYeQAtaxGC3XMj2fp4o5fEsV7hpKLkzFNVUxn2kff8lJMWb5mm9J7KmcGbAhdLb1uZAb1wLmvK2Q1v//qkRtHNVQ2usYzdD2jLC0/LFEkZLNRrnLHc0Gn72VtFA75oSfQxBAnX+SlHn9ZcZXtaSzOBUXdWw== service@unraveltec
EOF
chmod 700 ${ROOTFS_DIR}/root/.ssh
chmod 600 ${ROOTFS_DIR}/root/.ssh/authorized_keys

# Copy unpackaged Stuff
cp -r rootfs/* ${ROOTFS_DIR}
chmod 600 ${ROOTFS_DIR}/etc/mysql/reset.cnf

# read out hwclock as early as possible
# ln -f -s /etc/systemd/system/hwclock-early.service ${ROOTFS_DIR}/etc/systemd/system/sysinit.target.wants/hwclock-early.service

# convenience
sed -i 's|bash|zsh|' ${ROOTFS_DIR}/etc/passwd

#disable serial console
sed -i 's|console=serial0,115200||' ${ROOTFS_DIR}/boot/cmdline.txt

newhostname="IoT-Watchdog"
echo "$newhostname" > ${ROOTFS_DIR}/etc/hostname
sed -i "s/raspberrypi/$newhostname/" ${ROOTFS_DIR}/etc/hosts

# apache mods
cd ${ROOTFS_DIR}/etc/apache2/mods-enabled
ln -f -s ../mods-available/headers.load
ln -f -s ../mods-available/rewrite.load
ln -f -s ../mods-available/proxy.conf
ln -f -s ../mods-available/proxy_html.conf
ln -f -s ../mods-available/proxy.load
ln -f -s ../mods-available/proxy_html.load
ln -f -s ../mods-available/proxy_http.load
