#!/bin/bash

for i in hisat2_idx.tar.gz gtf.tar.gz fasta.tar.gz ; do
    aws --profile jhu-langmead s3 cp ${i} s3://recount-pump/ref/hg38/${i}
done
