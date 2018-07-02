#!/bin/sh

set -ex

docker-compose rm -f
docker-compose up --abort-on-container-exit
