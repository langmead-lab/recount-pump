#!/bin/bash

d=$(dirname $0)

IMAGE=$(cat ${d}/image.txt)

docker run -it \
    -v `pwd`:/work \
    $* --name recount-populate --rm ${IMAGE} /bin/bash
