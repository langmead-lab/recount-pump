#!/bin/sh

db=recount

if [ -n "$1" ] ; then
    db=$1
fi

./connect.sh postgres "CREATE DATABASE ${db} WITH OWNER = 'recount';"
