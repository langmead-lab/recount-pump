#!/bin/bash

set -ex

minio server /data &
pid=$!
/tmp/wait-for-it.sh localhost:9000
sleep 2
mv /tmp/staging/* /data/
wait $pid
