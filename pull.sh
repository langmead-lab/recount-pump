#!/bin/sh

ID=benlangmead
IMAGE=recount-pump
VER=0.0.1

docker pull $* ${ID}/${IMAGE}:${VER}
