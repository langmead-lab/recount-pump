#!/bin/sh

db=recount

if [ -n "$1" ] ; then
    db=$1
fi

./drop_db.sh "${db}" && ./create_db.sh "${db}"
