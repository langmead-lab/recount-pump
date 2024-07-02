#!/usr/bin/env bash
#Main multi-Pump runner script:
#1) formats and mounts SSDs
#2) downloads Monorail Pump references to SSD
#3) starts N Pump workers in parallel
#Assumes the following ENV vars are set:
#a) REF (hg38 or grcm38, required)
#b) NUM_WORKERS (number of concurrent workers to start, default: 16)
#c) NUM_CORES (maximum number of CPUs to use per worker, default: 8)
#d) SSD_MIN_SIZE (minimum size of local SSDs, default: 600GBs)
set -exo pipefail
dir=$(dirname $0)
if [[ -n $DEBUG ]]; then
    sleep 1d
fi

DEFAULT_NUM_WORKERS=16 #if we have enough cores + SSD space
DEFAULT_SSD_MIN_SIZE=600000000000
DEFAULT_NUM_CORES=8
if [[ -z $REF ]]; then
    echo "no REF set, terminating early!"
    exit -1
fi

#check for # of processors to determine instance type being run on:
num_procs=$(fgrep processor /proc/cpuinfo | wc -l)
if [[ $num_procs -eq 32 ]]; then
    DEFAULT_NUM_WORKERS=8
fi
if [[ $num_procs -eq 48 ]]; then
    DEFAULT_NUM_WORKERS=12
fi

if [[ -z $NUM_WORKERS ]]; then
    export NUM_WORKERS=$DEFAULT_NUM_WORKERS
fi
if [[ -z $NUM_CORES ]]; then
    export NUM_CORES=$DEFAULT_NUM_CORES
fi
if [[ -z $SSD_MIN_SIZE ]]; then
    export SSD_MIN_SIZE=$DEFAULT_SSD_MIN_SIZE
fi

user=$(whoami)
#check for local SSDs, creates file local_disks.txt
set +eo pipefail
sudo /usr/bin/time -v /bin/bash -x $dir/check_and_create_fs_for_ephemeral_disks.sh
set -eo pipefail

num_ssds=$(cat local_disks.txt | wc -l)
if [[ $num_ssds -eq 0 ]]; then
    export NO_SSD=1
    sudo mkdir /work1
    sudo chown ubuntu /work1
    sudo chmod u+rwx /work1
fi

#2) download Pump references to SSD
if [[ ! -d /work1/ref/${REF} ]]; then
    orgn="human"
    if [[ $REF == "grcm38" ]]; then
        orgn="mouse"
    fi
    mkdir -p /work1/ref
    pushd /work1/ref
    if [[ -z $NO_SSD ]]; then
        #run the multi-threaded retrieval of the minimal set of indexes (just STAR, annotation, and FASTA sequence) ~3m:20s
        /usr/bin/time -v $dir/get_ref_indexes_fast.sh $REF > get_ref_indexes_fast.sh.run 2>&1
    else
        #stream STAR index to FIFO version ~4m
        /usr/bin/time -v /bin/bash -x $dir/stream_STAR_indexes_from_S3.sh s3://neuro-recount-ds/recount3/$org/annotations/ref $REF        
    fi
    popd
fi 

#3) start N concurrent Pump workers
export REF_DIR=/work1/ref
pushd /work1
mkdir -p /work1/runs
if [[ $num_ssds -gt 1 ]]; then
    mkdir -p /work2/runs
fi
echo -n "" > worker.jobs
idx=2
for i in $( seq 1 $NUM_WORKERS ); do
    #alternate SSD to write job on
    if [[ $idx -eq 1 && $num_ssds -gt 1 ]]; then
        idx=2
    else
        idx=1
    fi
    echo "/usr/bin/time -v /bin/bash -x $dir/worker.sh /work${idx} > /work${idx}/runs/w${i}.run 2>&1" >> worker.jobs
done
cat worker.jobs
/usr/bin/time -v parallel -j${NUM_WORKERS} < worker.jobs > worker.jobs.run 2>&1
