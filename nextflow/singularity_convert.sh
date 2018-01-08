#!/bin/sh

docker pull singularityware/docker2singularity
docker run \
    -v /var/run/docker.sock:/var/run/docker.sock \
    -v $PWD:/output \
    --privileged -t --rm \
    singularityware/docker2singularity \
    benlangmead/recount-pump
