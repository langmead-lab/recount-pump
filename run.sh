#!/bin/bash

d=$(dirname $0)

IMAGE=$(cat ${d}/image.txt)

docker run -it $* --name recount ${IMAGE} /bin/bash
