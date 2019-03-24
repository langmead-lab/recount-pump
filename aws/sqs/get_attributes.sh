#!/bin/bash

INI_FILE="creds/queue.ini"
if [[ ! -f ${INI_FILE} ]] ; then
    echo "Could not find creds/queue.ini"
    echo "Please run from a project directory with a creds subdirectory as created by make_creds.py"
    exit 1
fi

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

if [ -z "${url}" ] ; then
    echo "No URL" && exit 1
fi

aws --profile ${profile} \
    --region ${region} \
    sqs \
    get-queue-attributes \
    --queue-url ${url} \
    --attribute-names All
