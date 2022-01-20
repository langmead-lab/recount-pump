#!/bin/sh

IMAGE=$(cat image.txt)
VER=$(cat ver.txt)

docker push $* ${IMAGE}:${VER}
#don't push latest anymore, don't want to automatically overwrite stable, public image
#docker push $* ${IMAGE}:latest
