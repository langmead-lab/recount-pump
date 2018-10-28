#!/usr/bin/env bash

syns=""
syns="${syns} syn17016853"  # hisat2 index
syns="${syns} syn17016854"  # STAR index
syns="${syns} syn17016851"  # fasta
syns="${syns} syn17016852"  # gtf
syns="${syns} syn17016855"  # UCSC tracks

for syn in ${syns} ; do
    synapse get ${syn}
done
