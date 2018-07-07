#!/bin/sh

docker run --rm --name postgres-recount \
    -e POSTGRES_USER=recount \
    -e POSTGRES_PASSWORD=recount-postgres \
    -e POSTGRES_DB=recount-test \
    -p 5432:5432 -d postgres:10.4
