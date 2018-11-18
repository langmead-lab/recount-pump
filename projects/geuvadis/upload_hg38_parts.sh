#!/bin/bash

for i in star_idx.tar.gz gtf.tar.gz fasta.tar.gz ; do
    aws --profile jhu-langmead s3 cp --acl public-read ${i} s3://recount-ref/hg38/${i}
done
