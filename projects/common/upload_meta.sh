#!/bin/bash

d=$(dirname $0)

study=$(grep '^study' project.ini | cut -d"=" -f2 | tr -d '[:space:]')

if [[ -f ${study}.json.gz ]] ; then
    echo "Uploading JSON..."
    aws --profile jhu-langmead s3 cp \
        ${study}.json.gz \
        s3://recount-pump-experiments/${study}/${study}.json.gz
elif [[ -f ${study}.txt ]] ; then
    echo "Uploading TXT..."
    aws --profile jhu-langmead s3 cp \
        ${study}.txt \
        s3://recount-pump-experiments/${study}/${study}.txt
else
    echo "Neither JSON nor TXT found"
    exit 1
fi
