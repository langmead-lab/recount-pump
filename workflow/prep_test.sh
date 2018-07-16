#!/bin/sh

set -ex

url=https://s3.amazonaws.com/recount-pump/ref

for species in ce10 ; do    
    mkdir -p ${species}
    for i in hisat2_idx.tar.gz fasta.tar.gz gtf.tar.gz ; do
        wget -q -O ${species}/${i} ${url}/${species}/${i}
    done
    
    cd ${species}
    for i in *.tar.gz ; do tar zxf $i ; done
    cd ..
done
