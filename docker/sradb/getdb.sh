#!/bin/bash

d=`dirname $0`

set -ex

IMAGE=$(cat $d/image.txt)
CONTAINER_NAME=$(basename ${IMAGE})
DB_DIR=$(mkdir -p ${d}/db && cd ${d}/db && pwd)

docker run --rm -it --name ${CONTAINER_NAME} \
     -v ${DB_DIR}:/db \
     --entrypoint Rscript \
     ${IMAGE} /getdb.R
