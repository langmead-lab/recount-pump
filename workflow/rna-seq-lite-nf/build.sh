#!/bin/sh

IMAGE=$(cat image.txt)
VER=0.0.3

docker build $* \
    --cache-from ${IMAGE}:latest \
    --tag ${IMAGE}:${VER} \
    --tag ${IMAGE}:latest \
    .
