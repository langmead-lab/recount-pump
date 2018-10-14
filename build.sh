#!/bin/bash

d=$(dirname $0)

IMAGE=$(cat ${d}/image.txt)
VER=$(cat ${d}/ver.txt)

docker build $* \
    --cache-from ${IMAGE}:${VER} \
    --tag ${IMAGE}:${VER} \
    --tag ${IMAGE}:latest \
    ${d}
