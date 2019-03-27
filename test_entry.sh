#!/bin/bash

set -ex

# Dockerfile copies the recount-pump working copy to /code
cd /code
./wait-for-it.sh elasticmq:9324 -t 30
./wait-for-it.sh s3:9000 -t 30
./wait-for-it.sh db:5432 -t 30

sleep 15
# TODO: more sophisticated tests to see if the services are up?

echo '*** Starting (unit tests) ***'
./unit_test.sh
echo '*** SUCCESS (unit tests) ***'

echo '*** Starting (end-to-end tests) ***'
./e2e_test.sh
echo '*** SUCCESS (end-to-end tests) ***'
