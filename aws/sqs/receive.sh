#!/bin/bash

INI_FILE="${HOME}/.recount/queue_aws.ini"

profile=$(grep '^aws_profile' ${INI_FILE} | cut -d"=" -f2 | tr -d '[:space:]')
region=$(grep '^region' ${INI_FILE} | cut -d"=" -f2 | tr -d '[:space:]')
queue_name=stage_2

if [ -n "$1" ] ; then
    queue_name=$1
fi

get_url() {
    aws --profile ${profile} \
	--region ${region} \
	sqs \
	get-queue-url \
	--queue-name "${queue_name}"
}

url=$(get_url | grep QueueUrl | sed 's/^[^:]*://' | sed 's/"//g')

echo "Got url: ${url}"

aws --profile ${profile} \
    --region ${region} \
    sqs \
    receive-message \
    --queue-url ${url} \
    --attribute-names All \
    --max-number-of-messages 1 \
    --visibility-timeout 1
