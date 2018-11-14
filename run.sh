#!/bin/bash

d=$(dirname $0)

IMAGE=$(cat ${d}/image.txt)

docker run -it \
    --privileged \
    --cap-add=SYS_ADMIN \
    -v `pwd`:/work \
    -v /var/run/docker.sock:/var/run/docker.sock \
    $* --name recount --rm ${IMAGE} /bin/bash
