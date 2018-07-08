#!/bin/sh

cp rna_seq.nf rna_seq.bash container/

ID=benlangmead
IMAGE=recount-pump-nextflow
VER=0.0.1

docker build $* \
    --cache-from ${ID}/${IMAGE}:latest \
    --tag ${ID}/${IMAGE}:${VER} \
    --tag ${ID}/${IMAGE}:latest \
    .
