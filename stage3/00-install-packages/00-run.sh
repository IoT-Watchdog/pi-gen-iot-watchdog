#!/bin/bash

cp influxdb.key ${ROOTFS_DIR}/influxdb.key

mkdir -p ${ROOTFS_DIR}/root/debs/
cp -ra deb-pkgs/* ${ROOTFS_DIR}/root/debs/
