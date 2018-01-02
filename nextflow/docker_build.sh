#!/bin/sh

cp rna_seq.nf container/rna_seq.nf
docker build -t benlangmead/recount-pump container
