#!/bin/bash

set -eu

source common.sh

SIEMENS_DIR=/mnt/siemens

# Check if Aardwolf directory is mounted
ls $AARDWOLF_DIR || error_msg "$AARDWOLF_DIR directory is not mounted"

# Check if results directory is mounted
ls $RESULTS_DIR || error_msg "$RESULTS_DIR directory is not mounted"

cp plugins.yml tools/plugins.yml
cp $RESULTS_DIR/plugins.yml tools/plugins.yml || true  # if does not exist, default will be used

# Check if siemens directory is mounted
ls $SIEMENS_DIR || error_msg "$SIEMENS_DIR directory is not mounted"

cp $SIEMENS_DIR/*.tar.gz siemens

run() {
    program=$1
    name=$(basename $program .tar.gz)

    shift
    ignore=$@

    # Used in sir.py script.
    export DATA_DIR_ID=$BASHPID

    python sir.py prepare $ROOTDIR/siemens/$program
    RESULTS_FILE=$RESULTS_DIR/$name.csv RAW_RESULTS_DIR=$RESULTS_DIR/$name python sir.py runall $ignore
}

cp -r tools $WORKDIR
pushd $WORKDIR/tools

run printtokens_2.0.tar.gz v4 v6 &
run printtokens2_2.0.tar.gz v10 &
run replace_2.1.tar.gz v8 v16 v32 &
run schedule_2.0.tar.gz v1 v6 v9 &
run schedule2_2.0.tar.gz v9 &
run tcas_2.0.tar.gz v38 &
run totinfo_2.0.tar.gz &

popd

# Wait for all spawned jobs
for job in `jobs -p`
do
    wait $job
done

clean_workdir
