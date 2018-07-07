#!/bin/sh

cp rna_seq.nf rna_seq.bash container/

docker build \
    --tag benlangmead/recount-pump-nextflow \
    --cache-from benlangmead/recount-pump-nextflow \
    container
