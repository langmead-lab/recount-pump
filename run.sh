#!/bin/sh

IMAGE=$(cat image.txt)

docker run -it $* ${IMAGE} /bin/bash
