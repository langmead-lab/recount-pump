#!/bin/sh

[ -z "${1}" ] && echo "Specify tool name" && exit 1

sudo docker push benlangmead/${1}
