#!/bin/sh

# Just the following gives "ERROR: cannot drop the currently open database"
#./connect.sh postgres 'DROP DATABASE IF EXISTS recount;'

INI_FILE="${HOME}/.recount/db_aws.ini"

username=$(grep '^user' ${INI_FILE} | cut -d"=" -f2 | tr -d '[:space:]')
password=$(grep '^pass' ${INI_FILE} | cut -d"=" -f2 | tr -d '[:space:]')
port=$(grep '^port' ${INI_FILE} | cut -d"=" -f2 | tr -d '[:space:]')
host=$(grep '^host' ${INI_FILE} | cut -d"=" -f2 | tr -d '[:space:]')
db=recount

if [[ -n "$1" ]] ; then
    db=$1
fi

PGPASSWORD=${password} dropdb \
    -h ${host} \
    -p ${port} \
    -U ${username} \
    ${db}
