#!/bin/bash

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
    create-db-subnet-group \
    --db-subnet-group-name ${name} \
    --db-subnet-group-description "For ${name} DB" \
    --subnet-ids ${subnet1} ${subnet2} \
    --tags Key=Application,Value=recount

aws rds --profile ${profile} --region ${region} \
    create-db-instance \
    --db-name ${name} \
    --db-instance-identifier ${name} \
    --db-instance-class ${instance} \
    --engine postgres \
    --master-username ${username} \
    --master-user-password ${password} \
    --port ${port} \
    --engine-version "10.4" \
    --publicly-accessible \
    --allocated-storage 20 \
    --tags Key=Application,Value=recount
# security group?
