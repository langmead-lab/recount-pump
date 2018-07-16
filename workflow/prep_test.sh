#!/bin/sh

set -ex

species=ce10
url=https://s3.amazonaws.com/recount-pump/ref

mkdir -p ref/${species}
for i in hisat2_idx.tar.gz fasta.tar.gz gtf.tar.gz ; do
    wget -q -O ref/${species}/${i} ${url}/${species}/${i}
done

cd ref/ce10
for i in *.tar.gz ; do tar zxvf $i ; done
