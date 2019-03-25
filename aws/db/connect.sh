#!/bin/bash

INI_FILE="creds/db.ini"
if [[ ! -f ${INI_FILE} ]] ; then
    echo "Could not find creds/db.ini"
    echo "Please run from a project directory with a creds subdirectory as created by make_creds.py"
    exit 1
fi

username=$(grep '^user' ${INI_FILE} | cut -d"=" -f2 | tr -d '[:space:]')
password=$(grep '^pass' ${INI_FILE} | cut -d"=" -f2 | tr -d '[:space:]')
port=$(grep '^port' ${INI_FILE} | cut -d"=" -f2 | tr -d '[:space:]')
host=$(grep '^host' ${INI_FILE} | cut -d"=" -f2 | tr -d '[:space:]')
dbname=recount
args=
if [[ -n "$1" ]] ; then
    dbname=$1
    shift
    args="-c"
fi

PGPASSWORD=${password} psql \
    -h ${host} \
    -p ${port} \
    -U ${username} \
    -d ${dbname} \
    ${args} "${*}"
