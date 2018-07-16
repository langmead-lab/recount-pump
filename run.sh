#!/bin/sh

ID=benlangmead
IMAGE=recount-pump
VER=0.0.1

docker run -it $* ${ID}/${IMAGE}:${VER} /bin/bash
