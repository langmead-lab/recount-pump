#!/bin/bash

d=$(dirname $0)

IMAGE=$(cat ${d}/image.txt)

docker pull --all-tags $* ${IMAGE}
