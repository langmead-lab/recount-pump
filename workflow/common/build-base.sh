#!/bin/sh

IMAGE=$(cat image.txt)
VER=$(cat ver.txt)

docker build $* \
    --cache-from ${IMAGE}:${VER} \
    --tag ${IMAGE}:${VER} \
    --tag ${IMAGE}:latest \
    .
