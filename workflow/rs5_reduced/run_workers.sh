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
DEFAULT_NUM_WORKERS=16
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


set +eo pipefail
df=$(df | fgrep "/work" | wc -l)
set -eo pipefail
#1) format and mount SSDs (but skip root)
user=$(whoami)
i=1
if [[ $df -eq 0 ]]; then
    for d in `lsblk -b | egrep -e '^nvme' | fgrep -v nvme0n1 | perl -ne '@f=split(/\s+/,$_,-1); next if($f[3] < '$SSD_MIN_SIZE'); print $f[0]."\n";'`; do 
        sudo mkfs -q -t ext4 /dev/$d
        sudo mkdir -p /work${i}
        sudo mount /dev/$d /work${i}/
        sudo chown -R $user /work${i}
        sudo chmod -R a+rw /work${i}
        i=$((i + 1))
    done
else
    i=$((df + 1))
fi
num_ssds=$((i - 1))

#2) download Pump references to SSD
if [[ ! -d /work1/ref/${REF} ]]; then
    orgn="human"
    if [[ $REF == "grcm38" ]]; then
        orgn="mouse"
    fi
    mkdir -p /work1/ref
    pushd /work1/ref
    #run the multi-threaded retrieval of the minimal set of indexes (just STAR, annotation, and FASTA sequence)
    /usr/bin/time -v $dir/get_ref_indexes_fast.sh $REF > get_ref_indexes_fast.sh.run 2>&1
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
