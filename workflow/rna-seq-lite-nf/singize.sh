#!/bin/sh

IMAGE=$(cat image.txt)

docker pull singularityware/docker2singularity >/dev/null
docker run \
    -v /var/run/docker.sock:/var/run/docker.sock \
    -v $PWD:/output \
    --privileged -t --rm \
    singularityware/docker2singularity \
    ${IMAGE}

nimg=$(ls *.img | wc -l)
if [ $nimg != 1 ] ; then
    echo "Unexpected number of .img files!"
    exit 1
fi

#img=$(ls *.img)
#zstd < ${img} > ${img}.zstd
#rm -f *.img