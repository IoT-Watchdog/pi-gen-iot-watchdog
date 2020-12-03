#!/bin/bash -e

# Aufbauend auf Stage 2
export PREV_ROOTFS_DIR=${PREV_ROOTFS_DIR/stage*\//stage2/}

if [ ! -d "${ROOTFS_DIR}" ]; then
	copy_previous
fi
