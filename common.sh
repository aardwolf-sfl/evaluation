#!/bin/bash

ROOTDIR=/root
RESULTS_DIR=/mnt/results
AARDWOLF_DIR=/mnt/aardwolf
WORKDIR=/mnt/workdir

# Create workdir directory for cases when it is not mounted
mkdir -p $WORKDIR

clean_workdir() {
    rm -rf $WORKDIR/*
    rm -rf $WORKDIR/.*
}

trap clean_workdir 0

error_msg () {
    clean_workdir
    echo "$@\texiting..."
    exit 1
}
