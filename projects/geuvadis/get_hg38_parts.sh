#!/usr/bin/env bash

syns=""
syns="${syns} syn11511600"  # hisat2 index
syns="${syns} syn11511596"  # fasta
syns="${syns} syn11511597"  # gtf

for syn in ${syns} ; do
    synapse get ${syn}
done
