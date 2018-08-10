#!/bin/sh

IMAGE=$(cat image.txt)

docker pull --all-tags $* ${IMAGE}
