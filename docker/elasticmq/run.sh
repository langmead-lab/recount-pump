#!/bin/bash

d=$(dirname $(realpath $0))
image=$(cat $d/image.txt)

docker run --rm --name elasticmq \
    -v $d/custom.conf:/opt/elasticmq.conf \
    -p 29324:9324 \
    -d ${image}
