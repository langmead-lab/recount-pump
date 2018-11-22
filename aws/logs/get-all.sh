#!/bin/bash

INI_FILE="$HOME/.recount/log.ini"
[[ ! -f $INI_FILE ]] && echo "Could not find INI file: ${INI_FILE}" && exit 1

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
