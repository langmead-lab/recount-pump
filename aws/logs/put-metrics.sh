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
         --filter-pattern "{ $.eventType = \"JsonSumTest\" }" \
         --metric-transformations metricName=JsonSumTest,metricNamespace=recount,metricValue=\$.amt,defaultValue=0

time=$(date +%s)

echo "Sending log event"

cat >/tmp/.event <<EOF
[
    {
        "timestamp": ${time},
        "message": "{\"eventType\": \"JsonSumTest\", \"amt\": 10}"
    }
]
EOF

aws logs put-log-events \
         --profile ${profile} \
         --log-group-name=${log_group} \
         --log-stream-name=${log_stream} \
         --log-events file:///tmp/.event
