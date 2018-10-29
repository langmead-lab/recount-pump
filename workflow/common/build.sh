#!/bin/bash

# must be run from the specific workflow directory

if [[ -f workflow.nf ]] ; then
    cp ../common/Dockerfile.nextflow Dockerfile
elif [[ -f Snakefile ]] ; then
    cp ../common/Dockerfile.snakemake Dockerfile
else
    echo "Can't tell what workflow system is being used" && exit 1
fi

cp ../common/workflow.bash .

IMAGE=$(cat image.txt)
VER=$(cat ver.txt)

docker build $* \
    --tag ${IMAGE}:${VER} \
    --tag ${IMAGE}:latest \
    .
