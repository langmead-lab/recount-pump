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

echo "Creating stream"

aws logs --profile ${profile} \
         --region=${region} \
         --log-group-name=${log_group} \
         --log-stream-name=${log_stream} \
         create-log-stream
