#!/bin/sh

set -ex

bucket=recount-pump

species=$1
[ -z "${species}" ] && echo "specify species shortname (e.g. dm6) as argument"

mkdir -p ${species}
url="https://s3.amazonaws.com/${bucket}/ref/${species}"

cd ${species}

files="star_idx.tar.gz unmapped_star_idx.tar.gz fasta.tar.gz gtf.tar.gz kallisto_index.tar.gz salmon_index.tar.gz"

for i in ${files} ; do
    wget -O ${i} ${url}/${i}
done

if [ -n "${2}" ] ; then
    for i in ${files} ; do
        tar zxvf $i
    done
fi

cd ..
