#!/bin/bash

d=$(dirname $0)

INI_FILE="$HOME/.recount/log.ini"
[[ ! -f $INI_FILE ]] && echo "Could not find INI file: ${INI_FILE}" && exit 1

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
    aws logs delete-metric-filter \
             --profile ${profile} \
             --region=${region} \
             --log-group-name=${log_group} \
             --filter-name "${shortname}"
done
