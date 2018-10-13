#!/bin/bash

# Queue name must be "unique within the scope of your queues"

INI_FILE="${HOME}/.recount/db_aws.ini"

profile=$(grep '^aws_profile' ${INI_FILE} | cut -d"=" -f2 | tr -d '[:space:]')
region=$(grep '^region' ${INI_FILE} | cut -d"=" -f2 | tr -d '[:space:]')
subnet1=$(grep '^subnet1' ${INI_FILE} | cut -d"=" -f2 | tr -d '[:space:]')
subnet2=$(grep '^subnet2' ${INI_FILE} | cut -d"=" -f2 | tr -d '[:space:]')
username=$(grep '^user' ${INI_FILE} | cut -d"=" -f2 | tr -d '[:space:]')
# note: password must be at least 8 characters
password=$(grep '^pass' ${INI_FILE} | cut -d"=" -f2 | tr -d '[:space:]')
port=$(grep '^port' ${INI_FILE} | cut -d"=" -f2 | tr -d '[:space:]')
name=recount
instance=db.t2.micro

set -ex

aws rds --profile ${profile} --region ${region} \
    create-queue \
    --attributes \
# TODO