#!/bin/bash

INI_FILE="${HOME}/.recount/db_aws.ini"

profile=$(grep '^aws_profile' ${INI_FILE} | cut -d"=" -f2 | tr -d '[:space:]')
region=$(grep '^region' ${INI_FILE} | cut -d"=" -f2 | tr -d '[:space:]')

aws rds \
    --profile ${profile} \
    --region ${region} \
    describe-db-instances
