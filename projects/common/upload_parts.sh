#!/bin/bash

d=$(dirname $0)

species=$(grep '^species_short' $d/project.ini | cut -d"=" -f2 | tr -d '[:space:]')

# TODO: get the list of reference files in a more parameterized way

for i in star_idx.tar.gz unmapped_hisat2_idx.tar.gz gtf.tar.gz fasta.tar.gz kallisto_index.tar.gz salmon_index.tar.gz ; do
    aws --profile jhu-langmead s3 cp --acl public-read ${i} s3://recount-ref/${species}/${i}
done
