#!/bin/sh

# From Minio Docker quickstart guide:
#
# Minio needs a persistent volume to store configuration and application data.
# However, for testing purposes, you can launch Minio by simply passing a
# directory (/data in the example below). This directory gets created in the
# container filesystem at the time of container start. But all the data is
# lost after container exits.

set -ex

CONTAINER_NAME=recount-minio
KEY_ID=$(grep aws_access_key_id credentials | cut -d' ' -f3)
SECRET=$(grep aws_secret_access_key credentials | cut -d' ' -f3)

docker run -p 9000:9000 -d --name ${CONTAINER_NAME} \
    -e "MINIO_ACCESS_KEY=${KEY_ID}" \
    -e "MINIO_SECRET_KEY=${SECRET}" \
    minio/minio server /data

docker logs ${CONTAINER_NAME}
