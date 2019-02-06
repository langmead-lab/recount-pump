#!/bin/sh

# Lightweight test script, assuming you're in a conda or other environment
# where all the required tools are installed

snakemake -j2 --config \
    input=../common/accessions.txt \
    output=output \
    temp=temp \
    ref=$HOME/recount-ref
