#!/bin/bash

INI_FILE="creds/log.ini"
if [[ ! -f ${INI_FILE} ]] ; then
    echo "Could not find creds/log.ini"
    echo "Please run from a project directory with a creds subdirectory as created by make_creds.py"
    exit 1
fi

profile=$(grep '^aws_profile' ${INI_FILE} | cut -d"=" -f2 | tr -d '[:space:]')
log_group=$(grep '^log_group' ${INI_FILE} | cut -d"=" -f2 | tr -d '[:space:]')
region=$(grep '^region' ${INI_FILE} | cut -d"=" -f2 | tr -d '[:space:]')
log_stream=$1
shift

if [[ -z "${log_stream}" ]] ; then
    log_stream=$(grep stream_name ~/.recount/log.ini | cut -d"=" -f2 | tr -d '[:space:]')
fi

set -ex

batch=1
aws logs get-log-events \
    --profile ${profile} \
    --region=${region} \
    --log-group-name=${log_group} \
    --log-stream-name=${log_stream} \
    --start-from-head \
    --output text \
    > logbatch_${batch}.txt

fwtok=$(head -n 1 logbatch_${batch}.txt | cut -f2,2)
batch=$((${batch} + 1))

while [[ -n $fwtok ]] ; do
    aws logs get-log-events \
        --profile ${profile} \
        --region=${region} \
        --log-group-name=${log_group} \
        --log-stream-name=${log_stream} \
        --next-token ${fwtok} \
        --output text \
        > logbatch_${batch}.txt
    newfwtok=$(head -n 1 logbatch_${batch}.txt | cut -f2,2)
    if [[ $newfwtok == $fwtok ]] ; then
        break
    fi
    fwtok=$newfwtok
    batch=$((${batch} + 1))
done

cat logbatch_*.txt | grep -v '^b/' > log.txt
rm -f logbatch_*.txt

echo "DONE"
