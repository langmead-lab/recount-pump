#!/bin/bash

d=$(dirname $0)

study=$(grep '^study' project.ini | cut -d"=" -f2 | tr -d '[:space:]')

aws --profile jhu-langmead s3 cp \
    ${study}.json.gz \
    s3://recount-pump-experiments/${study}/${study}.json.gz
