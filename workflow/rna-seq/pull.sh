#!/bin/sh

IMAGE=$(cat image.txt)

docker pull ${IMAGE}
