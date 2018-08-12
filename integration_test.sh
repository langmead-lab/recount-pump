#!/bin/sh

set -ex

rm -rf testing/output/*
docker-compose rm -f
docker-compose up --abort-on-container-exit
