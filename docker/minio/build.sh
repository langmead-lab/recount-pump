#!/bin/sh

d=`dirname $0`

IMAGE=$(cat ${d}/image.txt)
VER=$(cat ${d}/ver.txt)

rm -rf src
cp -r $d/../../src .
cp $d/../../requirements.txt .

docker build $* \
    --tag ${IMAGE}:${VER} \
    --tag ${IMAGE}:latest \
    .

rm -f requirements.txt
rm -rf src
