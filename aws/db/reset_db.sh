#!/usr/bin/env bash

d=$(dirname $0)
db=recount

if [[ -n "$1" ]] ; then
    db=$1
fi

${d}/drop_db.sh "${db}" && ${d}/create_db.sh "${db}"
