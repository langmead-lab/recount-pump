#!/bin/sh

set -ex

ref=$1

url=https://s3.amazonaws.com/recount-ref

for species in $ref ; do    
    mkdir -p ${species}
    for i in star_idx.tar.gz unmapped_hisat2_idx.tar.gz fasta.tar.gz gtf.tar.gz salmon_index.tar.gz ; do
        wget -q -O ${species}/${i} ${url}/${species}/${i}
    done
    
    cd ${species}
    for i in *.tar.gz ; do tar zxf $i ; done
    cd ..
done

mkdir -p singularity_cache
pushd singularity_cache
singularity pull docker://quay.io/benlangmead/recount-rs5:1.0.2
popd
