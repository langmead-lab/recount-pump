#!/bin/bash

INI_FILE="$HOME/.recount/log.ini"
[[ ! -f $INI_FILE ]] && echo "Could not find INI file: ${INI_FILE}" && exit 1

profile=$(grep '^aws_profile' ${INI_FILE} | cut -d"=" -f2 | tr -d '[:space:]')
log_group=$(grep '^log_group' ${INI_FILE} | cut -d"=" -f2 | tr -d '[:space:]')
region=$(grep '^region' ${INI_FILE} | cut -d"=" -f2 | tr -d '[:space:]')

aws logs describe-metric-filters \
    --profile ${profile} \
    --region=${region} \
    --log-group-name=${log_group}
