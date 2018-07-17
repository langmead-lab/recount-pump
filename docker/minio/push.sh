#!/bin/sh

IMAGE=$(cat image.txt)

docker push $* ${IMAGE}
