#!/bin/sh

set -ex

rm -rf testing/output/*
rm -rf testing/temp/*
docker-compose rm -f
docker-compose up --abort-on-container-exit
