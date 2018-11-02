#!/usr/bin/env bash

syns=""
syns="${syns} syn11640488"  # hisat2 index
syns="${syns} syn11640489"  # STAR index
syns="${syns} syn11640486"  # fasta
syns="${syns} syn11640487"  # gtf
syns="${syns} syn11640490"  # UCSC tracks

for syn in ${syns} ; do
    synapse get ${syn}
done
