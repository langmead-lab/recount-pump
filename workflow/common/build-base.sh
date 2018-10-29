#!/bin/sh

IMAGE=$(cat image.txt)
VER=$(cat ver.txt)

docker build $* \
    --tag ${IMAGE}:${VER} \
    --tag ${IMAGE}:latest \
    .
