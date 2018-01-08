#!/bin/sh

cp rna_seq.nf rna_seq.bash container/

docker build \
    --tag benlangmead/recount-pump \
    --cache-from benlangmead/recount-pump \
    container
