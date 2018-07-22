#!/bin/sh

IMAGE=$(cat image.txt)

docker run -it $* --name recount ${IMAGE} /bin/bash
