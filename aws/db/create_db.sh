#!/usr/bin/env bash

d=$(dirname $0)
db=recount

if [[ -n "$1" ]] ; then
    db=$1
fi

${d}/connect.sh postgres "CREATE DATABASE ${db} WITH OWNER = 'recount';"
