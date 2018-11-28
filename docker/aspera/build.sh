#!/bin/sh

d=`dirname $0`

IMAGE=$(cat ${d}/image.txt)
VER=$(cat ${d}/ver.txt)

docker build $* \
    --tag ${IMAGE}:${VER} \
    --tag ${IMAGE}:latest \
    .
