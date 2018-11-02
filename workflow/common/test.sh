#!/bin/sh

snakemake -j2 --config \
    input=../common/accessions.txt \
    output=output \
    temp=temp \
    ref=$HOME/recount-ref
