#!/bin/sh

cp rna_seq.nf rna_seq.bash container/
docker build -t benlangmead/recount-pump container
