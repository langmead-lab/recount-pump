#!/bin/bash

INI_FILE="${HOME}/.recount/db_aws.ini"

username=$(grep '^user' ${INI_FILE} | cut -d"=" -f2 | tr -d '[:space:]')
password=$(grep '^pass' ${INI_FILE} | cut -d"=" -f2 | tr -d '[:space:]')
port=$(grep '^port' ${INI_FILE} | cut -d"=" -f2 | tr -d '[:space:]')
host=$(grep '^host' ${INI_FILE} | cut -d"=" -f2 | tr -d '[:space:]')
dbname=recount

psql \
    -h ${host} \
    -p ${port} \
    -U ${username} \
    -d ${dbname}
