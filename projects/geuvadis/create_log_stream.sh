#!/bin/bash

profile=$(grep aws_profile ~/.recount/log.ini | cut -d"=" -f2 | tr -d '[:space:]')
log_group=$(grep log_group ~/.recount/log.ini | cut -d"=" -f2 | tr -d '[:space:]')
log_stream=$1
shift

if [[ -z "${log_stream}" ]] ; then
    log_stream=recount-pump-geuvadis
fi

aws logs --profile ${profile} \
         --log-group-name=${log_group} \
         --log-stream-name=${log_stream} \
         create-log-stream
