#!/bin/bash

set -eu

source common.sh

# Check if Aardwolf directory is mounted
ls $AARDWOLF_DIR || error_msg "$AARDWOLF_DIR directory is not mounted"

# Check if results directory is mounted
ls $RESULTS_DIR || error_msg "$RESULTS_DIR directory is not mounted"

cp $RESULTS_DIR/plugins.yml plugins.yml || true  # if does not exist, default will be used
cat plugins.yml >> libtiff/.aardwolf.yml
cat plugins.yml >> matplotlib/.aardwolf.yml

echo "output_dir: $WORKDIR/.aardwolf" >> libtiff/.aardwolf.yml
echo "output_dir: $WORKDIR/.aardwolf" >> matplotlib/.aardwolf.yml

mkdir -p raw

# libtiff
libtiff () {
    pushd libtiff

    make distclean || true
    rm -rf test/benchmark.txt $WORKDIR/.aardwolf
    mkdir $WORKDIR/.aardwolf

    unset AARDWOLF_DATA_DEST
    if test "$1" = aardwolf
    then
        export AARDWOLF_DATA_DEST=$WORKDIR/.aardwolf
    fi

    # Time + Memory

    if test "$1" = aardwolf
    then
        ./configure --with-aardwolf=$AARDWOLF_DIR CC=clang
        python patch_libtool.py
        cflags="-g -O0 -Xclang -load -Xclang $AARDWOLF_DIR/libAardwolfLLVM.so"
    else
        ./configure
        cflags="-g -O0 -Wall -W"
    fi
    make CFLAGS="$cflags" CC=clang

    for i in 1 2 3
    do
        make check || true
        mv test/benchmark.txt ../raw/libtiff_time_memory_$1_$i.txt
    done

    # Binary size

    du -b -d 0 libtiff/*.o tools/*.o > ../raw/libtiff_binary_$1.txt

    # Aardwolf plugins times

    if test "$1" = aardwolf
    then
        make distclean || true

        $AARDWOLF_DIR/aardwolf
        cat $WORKDIR/.aardwolf/aard.log | sed -E 's/.+perf: "([^"]+)" took (.+) secs/\1\t\2/' > ../raw/libtiff_aardwolf_times_1.txt

        for i in 2 3
        do
            $AARDWOLF_DIR/aardwolf --reuse
            cat $WORKDIR/.aardwolf/aard.log | sed -E 's/.+perf: "([^"]+)" took (.+) secs/\1\t\2/' > ../raw/libtiff_aardwolf_times_$i.txt
        done
    fi

    popd
}

# matplotlib
matplotlib_prepare () {
    pushd matplotlib

    pip install $AARDWOLF_DIR/aardwolf-0.1.0.tar.gz

    # Temporarily, the number of test files is limited to 30 because of high memory usage
    python tests.py --collect-only -q | cut -d':' -f1 | sort | uniq | grep lib | head -n 30 > tests.txt
    sed -i 's/- python tests.py || true/- python tests.py $(cat tests.txt) || true/' .aardwolf.yml

    # Probabilistic dependence does not work with matplotlib at the moment
    sed -i 's/- prob-graph/#/' .aardwolf.yml

    popd
}

matplotlib () {
    pushd matplotlib

    find lib -name '*.pyc' | xargs rm -f
    rm -rf benchmark.txt $WORKDIR/.aardwolf
    mkdir $WORKDIR/.aardwolf

    unset AARDWOLF_DATA_DEST
    if test "$1" = aardwolf
    then
        export AARDWOLF_DATA_DEST=$WORKDIR/.aardwolf
    fi

    # Time + Memory

    for i in 1 2 3
    do
        for test in $(cat tests.txt)
        do
            echo "Testing $test"
            env time --format '%e s ; %M kB' -ao benchmark.txt --quiet python tests.py $test || true
        done
        mv benchmark.txt ../raw/matplotlib_time_memory_$1_$i.txt
    done

    # Binary size

    find lib -name '*.pyc' | xargs du -b -d 0 --exclude 'lib/matplotlib/tests/*' --exclude 'lib/matplotlib/testing/*' --exclude 'lib/mpl_toolkits/tests/*' > ../raw/matplotlib_binary_$1.txt

    # Aardwolf plugins times

    if test "$1" = aardwolf
    then
        $AARDWOLF_DIR/aardwolf --ignore-corrupted
        cat $WORKDIR/.aardwolf/aard.log | sed -E 's/.+perf: "([^"]+)" took (.+) secs/\1\t\2/' > ../raw/matplotlib_aardwolf_times_1.txt

        for i in 2 3
        do
            $AARDWOLF_DIR/aardwolf --reuse --ignore-corrupted
            cat $WORKDIR/.aardwolf/aard.log | sed -E 's/.+perf: "([^"]+)" took (.+) secs/\1\t\2/' > ../raw/matplotlib_aardwolf_times_$i.txt
        done
    fi

    popd
}

process_data=$ROOTDIR/tools/scalability_data.py

libtiff baseline
python $process_data timem raw/libtiff_time_memory_baseline* > $RESULTS_DIR/libtiff_time_memory_baseline.csv
python $process_data binary raw/libtiff_binary_baseline* > $RESULTS_DIR/libtiff_binary_baseline.csv

libtiff aardwolf
python $process_data timem raw/libtiff_time_memory_aardwolf* > $RESULTS_DIR/libtiff_time_memory_aardwolf.csv
python $process_data binary raw/libtiff_binary_aardwolf* > $RESULTS_DIR/libtiff_binary_aardwolf.csv
python $process_data plugins raw/libtiff_aardwolf_times* > $RESULTS_DIR/libtiff_plugins.csv


matplotlib_prepare

matplotlib baseline
python $process_data timem raw/matplotlib_time_memory_baseline* > $RESULTS_DIR/matplotlib_time_memory_baseline.csv
python $process_data binary raw/matplotlib_binary_baseline* > $RESULTS_DIR/matplotlib_binary_baseline.csv

matplotlib aardwolf
python $process_data timem raw/matplotlib_time_memory_aardwolf* > $RESULTS_DIR/matplotlib_time_memory_aardwolf.csv
python $process_data binary raw/matplotlib_binary_aardwolf* > $RESULTS_DIR/matplotlib_binary_aardwolf.csv
python $process_data plugins raw/matplotlib_aardwolf_times* > $RESULTS_DIR/matplotlib_plugins.csv
