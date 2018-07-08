#!/bin/sh

ID=benlangmead
IMAGE=recount-pump
VER=0.0.1

docker build $* \
    --cache-from ${ID}/${IMAGE}:latest \
    --tag ${ID}/${IMAGE}:${VER} \
    --tag ${ID}/${IMAGE}:latest \
    .
