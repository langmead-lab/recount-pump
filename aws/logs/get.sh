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

aws logs --profile ${profile} \
         --region=${region} \
         --log-group-name=${log_group} \
         --log-stream-name=${log_stream} \
         --output text \
         get-log-events
