#!/bin/bash

INI_FILE="${HOME}/.recount/queue_aws.ini"

profile=$(grep '^aws_profile' ${INI_FILE} | cut -d"=" -f2 | tr -d '[:space:]')
region=$(grep '^region' ${INI_FILE} | cut -d"=" -f2 | tr -d '[:space:]')

aws --profile ${profile} \
    --region ${region} \
    sqs \
    list-queues
