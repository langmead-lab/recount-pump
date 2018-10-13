#!/bin/bash

profile=$(grep aws_profile ~/.recount/log.ini | cut -d"=" -f2 | tr -d '[:space:]')
log_group=$(grep log_group ~/.recount/log.ini | cut -d"=" -f2 | tr -d '[:space:]')
aws logs --profile ${profile} \
         --log-group-name=${log_group} \
         describe-log-streams
