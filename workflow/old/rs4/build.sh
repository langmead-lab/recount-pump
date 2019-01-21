#!/bin/bash

# must be run from the specific workflow directory

cp ../common/workflow.bash .
cp ../../experimental/bam2bigwig.py .

IMAGE=$(cat image.txt)
VER=$(cat ver.txt)

docker build $* \
    --tag ${IMAGE}:${VER} \
    --tag ${IMAGE}:latest \
    .
