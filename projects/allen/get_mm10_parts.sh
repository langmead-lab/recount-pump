#!/usr/bin/env bash

syns=""
syns="${syns} syn11511599"  # hisat2 index
syns="${syns} syn11511592"  # fasta
syns="${syns} syn11511593"  # gtf
syns="${syns} syn11511604"  # UCSC tracks

for syn in ${syns} ; do
    synapse get ${syn}
done
