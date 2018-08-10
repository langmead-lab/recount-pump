#!/bin/sh

IMAGE=$(cat image.txt)
VER=$(cat ver.txt)

docker push $* ${IMAGE}:${VER}
docker push $* ${IMAGE}:latest
