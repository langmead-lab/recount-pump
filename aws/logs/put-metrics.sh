#!/bin/bash

d=$(dirname $0)

profile=$(grep aws_profile ~/.recount/log.ini | cut -d"=" -f2 | tr -d '[:space:]')
log_group=$(grep log_group ~/.recount/log.ini | cut -d"=" -f2 | tr -d '[:space:]')
log_stream=$1

if [[ -z "${log_stream}" ]] ; then
    log_stream=$(grep stream_name ~/.recount/log.ini | cut -d"=" -f2 | tr -d '[:space:]')
fi

echo "Adding filters"

metrics=$(grep 'log.*COUNT_' $d/../../src/*.py | sed 's/.*COUNT/COUNT/' | sed 's/ .*//')
metrics="${metrics} $(grep 'echo "COUNT_' $d/../../workflow/*/Snakefile | sed 's/.*COUNT/COUNT/' | sed 's/ .*//')"
metrics=$(echo ${metrics} | sort -u)

echo "  found counters:"
echo "${metrics}"

for metric in ${metrics} ; do
    shortname=$(echo ${metric} | sed 's/^COUNT_//')
    echo "Name: ${metric}, short name: ${shortname}"
    aws logs put-metric-filter \
             --profile ${profile} \
             --log-group-name=${log_group} \
             --filter-name "${shortname}" \
             --filter-pattern "[ month, day, time, host, module, lab = \"${metric}\", amt ]" \
             --metric-transformations metricName=JsonSumTest,metricNamespace=recount,metricValue=\$amt,defaultValue=0
done
