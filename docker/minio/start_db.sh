#!/bin/bash

set -ex

[[ -z "${MINIO_ACCESS_KEY}" ]] && echo "MINIO_ACCESS_KEY must be set" && exit 1
[[ -z "${MINIO_SECRET_KEY}" ]] && echo "MINIO_SECRET_KEY must be set" && exit 1

# BTL: I don't quite understand why this is necessary.  Somehow the
# files in /data are living across container runs.  Might have to do
# with the VOLUME["/data"] directive in the base Dockerfile.
rm -rf /data/*
minio server /data &
pid=$!
/tmp/wait-for-it.sh localhost:9000

sleep 2
for i in /tmp/staging/* ; do
    mv ${i} /data/
done
du -sh /data
tree /data
wait ${pid}

echo "Finished waiting for minio server at pid=${pid}, all ready"
