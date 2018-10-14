#!/bin/bash

d=`dirname $0`

if [[ -f workflow.nf ]] ; then
    cp $d/Dockerfile.nextflow Dockerfile
elif [[ -f Snakefile ]] ; then
    cp $d/Dockerfile.snakemake Dockerfile
else
    echo "Can't tell what workflow system is being used" && exit 1
fi

cp $d/workflow.bash .

IMAGE=$(cat ${d}/image.txt)
VER=$(cat ${d}/ver.txt)

docker build $* \
    --cache-from ${IMAGE}:${VER} \
    --tag ${IMAGE}:${VER} \
    --tag ${IMAGE}:latest \
    ${d}
