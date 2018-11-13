#!/bin/bash

set -ex

cd /code
./wait-for-it.sh elasticmq:9324 -t 30
./wait-for-it.sh s3:9000 -t 30
./wait-for-it.sh db:5432 -t 30

cp -r /creds/.aws /root/
cp -r /creds/.recount /root/
cp -r /creds/.mc /root/
for i in $(ls /root/.*/*.override) ; do
    echo "*** Renaming ${i} ***"
    mv ${i} $(echo ${i} | sed 's/\.override$//')
done

sleep 5

# TODO: more sophisticated tests to see if the services are up?

echo '*** Starting (unit tests) ***'
./unit_test.sh
echo '*** SUCCESS (unit tests) ***'

echo '*** Starting (end-to-end tests) ***'
./e2e_test.sh
echo '*** SUCCESS (end-to-end tests) ***'
