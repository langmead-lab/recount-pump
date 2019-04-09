#!/bin/bash

d=$(dirname $0)

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

if [[ -z "${log_stream}" ]] ; then
    log_stream=$(grep stream_name ~/.recount/log.ini | cut -d"=" -f2 | tr -d '[:space:]')
fi

echo "Adding filters"

set -e

for metric in $($d/parse_counters.sh) ; do
    shortname=$(echo ${metric} | sed 's/^COUNT_//')
    echo "Name: ${metric}, short name: ${shortname}"
    aws logs put-metric-filter \
             --profile ${profile} \
             --region=${region} \
             --log-group-name=${log_group} \
             --filter-name "${shortname}" \
             --filter-pattern "[ month, day, time, host, module, lab = \"${metric}\", amt ]" \
             --metric-transformations metricName=${shortname},metricNamespace=recount,metricValue=\$amt,defaultValue=0
done
