#!/bin/sh

d=`dirname $0`

rm -rf src
cp -r $d/../../src .
cp $d/../../requirements.txt .

IMAGE=$(cat image.txt)
VER=0.0.3

docker build $* \
    --tag ${IMAGE}:${VER} \
    --tag ${IMAGE}:latest \
    .
