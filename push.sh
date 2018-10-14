#!/bin/bash

d=$(dirname $0)

IMAGE=$(cat ${d}/image.txt)
VER=$(cat ${d}/ver.txt)

docker push $* ${IMAGE}:${VER}
docker push $* ${IMAGE}:latest
