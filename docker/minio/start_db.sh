#!/bin/bash

set -ex

[ -z "$MINIO_ACCESS_KEY" ] && echo "MINIO_ACCESS_KEY must be set" && exit 1
[ -z "$MINIO_SECRET_KEY" ] && echo "MINIO_SECRET_KEY must be set" && exit 1

minio server /data &
pid=$!
/tmp/wait-for-it.sh localhost:9000

sleep 2
mv /tmp/staging/* /data/
du -sh /data
tree /data
wait $pid
