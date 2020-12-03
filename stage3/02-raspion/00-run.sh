#!/bin/bash -e

cp -r ../../externals/ctraspion ${ROOTFS_DIR}/opt/
cp ntopng/dump.rdb ${ROOTFS_DIR}/var/lib/redis/dump.rdb
