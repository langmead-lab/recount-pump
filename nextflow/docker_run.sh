#!/bin/sh

IMAGE="benlangmead/recount-pump"

set -ex

test -n ${RECOUNT_REFDIR}
test -d ${RECOUNT_REFDIR}

docker run \
    -v `pwd`:/app \
    -v ${RECOUNT_REFDIR}:/ref \
    ${IMAGE} \
    /bin/bash -c \
    "source activate rnaseq_v0 && bash /home/biodocker/bin/rna_seq.bash /app/accessions.txt"
