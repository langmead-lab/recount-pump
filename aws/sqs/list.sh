#!/bin/bash

INI_FILE="creds/queue.ini"
if [[ ! -f ${INI_FILE} ]] ; then
    echo "Could not find creds/queue.ini"
    echo "Please run from a project directory with a creds subdirectory as created by make_creds.py"
    exit 1
fi

profile=$(grep '^aws_profile' ${INI_FILE} | cut -d"=" -f2 | tr -d '[:space:]')
region=$(grep '^region' ${INI_FILE} | cut -d"=" -f2 | tr -d '[:space:]')
endpoint=$(grep '^endpoint' ${INI_FILE} | cut -d"=" -f2 | tr -d '[:space:]')

if [[ -n "${endpoint}" ]] ; then
    endpoint="--endpoint ${endpoint}"
fi

aws --profile ${profile} \
    --region ${region} \
    ${endpoint} \
    sqs \
    list-queues
