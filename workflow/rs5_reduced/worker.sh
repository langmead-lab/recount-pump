#!/usr/bin/env bash
#Main single-Pump runner script:
#in a loop:
#1) checks for job on pump SQS (one study)
#2) dequeues job and gets date_time stamp at time of dequeue
#3) calls workflow.bash on study
#4) on success, copies results into temporary S3 location
#5) regardless of status of 4/5, removes results and temporary files from local SSDs to keep usage down
#6) repeat
#Assumes the following ENV vars are set:
#a) REF (hg38 or grcm38, required)
#b) Q (queue, usually SQS URL) to retrieve jobs from (1 per study to unify, default: monorail_batch on SQS)
#c) DOCKER_IMAGE (docker image of Pump to use, default: 1.1.3)
#d) REF_DIR (references directory, default: /work1/ref)
#e) NUM_CORES (maximum number of CPUs to use per worker, default: 8)
#f) OUTPUT_DIR_GLOBAL (should be full path, where to write the unifier outputs temporarily, before copying back to S3, default: /work1/pump/$study)
#g) S3_OUTPUT (where to upload the pump results to on S3, default: s3://monorail-batch/pump_outputs/)
set -exo pipefail
dir=$(dirname $0)

#filesystem to write temporary output to
#e.g. /work2
fs=$1

if [[ -z $fs ]]; then
    export fs="/work1"
fi

if [[ -z $REF ]]; then
    echo "no REF set, terminating early!"
    exit -1
fi
if [[ -z $Q ]]; then
    export Q="https://sqs.us-east-1.amazonaws.com/315553526860/monorail_batch_pump"
fi
if [[ -z $DOCKER_IMAGE ]]; then
    export DOCKER_IMAGE="315553526860.dkr.ecr.us-east-1.amazonaws.com/recount-pump-aarch64:1.1.3"
fi
if [[ -z $REF_DIR ]]; then
    export REF_DIR=/work1/ref
fi
if [[ -z $NUM_CORES ]]; then
    export NUM_CORES=8
fi
if [[ -z $OUTPUT_DIR_GLOBAL ]]; then
    export OUTPUT_DIR_GLOBAL="$fs/pump"
fi
if [[ -z $S3_OUTPUT ]]; then
    export S3_OUTPUT="s3://monorail-batch/pump_outputs6"
fi

#1) check for new studies on the queue
msg_json=$(aws sqs receive-message --queue-url $Q)
while [[ -n $msg_json ]]; do
    set +eo pipefail
    handle=$(echo "$msg_json" | fgrep '"ReceiptHandle":' | cut -d'"' -f 4)
    sample_study=$(echo "$msg_json" | fgrep '"Body":' | cut -d'"' -f 4)
    set -eo pipefail
    if [[ -z $handle || -z $sample_study ]]; then
        echo "ERROR: didn't find either a handle or a sample_study in SQS message: $msg_json.  skipping"
        aws sqs delete-message --queue-url $queue --receipt-handle $handle
        msg_json=$(aws sqs receive-message --queue-url $Q)
        continue
    fi
    date=$(date +%Y%m%d_%s)
    sample=$(echo "$sample_study" | cut -d'|' -f 1)
    study=$(echo "$sample_study" | cut -d'|' -f 2)
    lo=${study: -2}
    export OUTPUT_DIR=$OUTPUT_DIR_GLOBAL/${sample}.${date}
    rm -rf $OUTPUT_DIR
    mkdir -p $OUTPUT_DIR
    pushd $OUTPUT_DIR
    export WORKING_DIR=$OUTPUT_DIR
    #2) download list of sample/run accessions for the study already on S3
    #/usr/bin/time -v aws s3 cp $s3_accessions_path/$lo/${study}.txt ./
    mkdir -p runs
    #3) Run Pump
    #this is for the SPOT shutdown monitoring script to know which runs are in process
    /bin/bash $dir/monorail_pump_log.sh $sample $study START
    echo "$sample" > /dev/shm/PUMP_RUN.${sample}
    #TODO: double check params
    /usr/bin/time -v /bin/bash -x $dir/run_recount_pump_within_container.sh $sample $study $REF $NUM_CORES $REF_DIR > run_recount_pump_within_container.sh.run 2>&1
    success=$(egrep -e '^SUCCESS$' run_recount_pump_within_container.sh.run)
    if [[ -z $success ]]; then
        echo "pump failed for $sample in $study, skipping"
        /bin/bash $dir/monorail_pump_log.sh $sample $study PUMP_FAILED
        msg_json=$(aws sqs receive-message --queue-url $Q)
        continue
    fi
    /bin/bash $dir/monorail_pump_log.sh $sample $study PUMP_DONE
    #4) copy pump results back to S3
    lo2=${sample: -2}
    /usr/bin/time -v aws s3 cp --recursive `pwd`/output/ $S3_OUTPUT/$lo/$study/$lo2/${sample}.${date}/ > s3upload.run 2>&1
    #get next message repeat
    aws sqs delete-message --queue-url $Q --receipt-handle $handle
    rm -f /dev/shm/PUMP_RUN.${sample}
    /bin/bash $dir/monorail_pump_log.sh $sample $study END
    msg_json=$(aws sqs receive-message --queue-url $Q)
done
