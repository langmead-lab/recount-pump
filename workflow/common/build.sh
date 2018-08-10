#!/bin/sh

d=`dirname $0`

cp $d/Dockerfile .
cp $d/workflow.bash .

IMAGE=$(cat image.txt)
VER=$(cat ver.txt)

docker build $* \
    --cache-from ${IMAGE}:${VER} \
    --tag ${IMAGE}:${VER} \
    --tag ${IMAGE}:latest \
    .
