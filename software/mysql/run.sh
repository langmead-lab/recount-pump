#!/bin/sh

docker run --rm -p 3306:3306 -d \
    --name mysql-recount \
    benlangmead/recount-mysql
