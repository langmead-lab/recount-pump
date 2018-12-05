#!/bin/sh

set -ex

url=https://s3.amazonaws.com/recount-ref

for species in ce10 ; do    
    mkdir -p ${species}
    for i in star_idx.tar.gz hisat2_idx.tar.gz unmapped_star_idx.tar.gz fasta.tar.gz gtf.tar.gz kallisto_index.tar.gz salmon_index.tar.gz ; do
        wget -q -O ${species}/${i} ${url}/${species}/${i}
    done
    
    cd ${species}
    for i in *.tar.gz ; do tar zxf $i ; done
    cd ..
done
