#!/bin/sh

set -ex

cd /code
./wait-for-it.sh elasticmq:9324 -t 30
./wait-for-it.sh s3:9000 -t 30
./wait-for-it.sh db:5432 -t 30

echo '*** Starting (unit tests) ***'
./unit_test.sh
echo '*** SUCCESS (unit tests) ***'

echo '*** Starting (end-to-end tests) ***'
./e2e_test.sh
echo '*** SUCCESS (end-to-end tests) ***'
