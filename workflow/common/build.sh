#!/bin/bash

# must be run from the specific workflow directory

IMAGE=$(cat image.txt)
VER=$(cat ver.txt)

docker build $* -f Dockerfile.slim\
    --tag ${IMAGE}:${VER} \
    .
