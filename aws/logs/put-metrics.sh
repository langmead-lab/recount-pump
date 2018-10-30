#!/bin/bash

profile=$(grep aws_profile ~/.recount/log.ini | cut -d"=" -f2 | tr -d '[:space:]')
log_group=$(grep log_group ~/.recount/log.ini | cut -d"=" -f2 | tr -d '[:space:]')
log_stream=$1

if [[ -z "${log_stream}" ]] ; then
    log_stream=$(grep stream_name ~/.recount/log.ini | cut -d"=" -f2 | tr -d '[:space:]')
fi

echo "Adding filter"

aws logs put-metric-filter \
         --profile ${profile} \
         --log-group-name=${log_group} \
         --filter-name JsonTest \
         --filter-pattern "[ month, day, time, host, module, lab = \"COUNT\", name, amt ]" \
         --metric-transformations metricName=JsonSumTest,metricNamespace=recount,metricValue=\$amt,defaultValue=0
