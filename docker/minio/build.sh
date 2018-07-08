#!/bin/sh

d=`dirname $0`

rm -rf src
cp -r $d/../../src .
cp $d/../../requirements.txt .

ID=benlangmead
IMAGE=recount-minio
VER=0.0.1

docker build $* \
    --cache-from ${ID}/${IMAGE}:latest \
    --tag ${ID}/${IMAGE}:${VER} \
    --tag ${ID}/${IMAGE}:latest \
    .
