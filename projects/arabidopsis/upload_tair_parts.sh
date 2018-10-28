#!/bin/bash

species=TAIR10_Araport11

for i in hisat2_idx.tar.gz star_idx.tar.gz gtf.tar.gz fasta.tar.gz ucsc_tracks.tar.gz ; do
    aws --profile jhu-langmead s3 cp --acl public-read ${i} s3://recount-ref/${species}/${i}
done
