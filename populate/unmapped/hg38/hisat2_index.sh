#!/bin/sh

set -ex

test -n "$(ls *.fna)"

cat *.fna > virus.fa

OUTPUT=unmapped_hisat2_idx
rm -rf ${OUTPUT}
mkdir -p ${OUTPUT}

hisat2-build \
    --threads 8 \
    virus.fa \
    ${OUTPUT}/genome

tar -zcvf unmapped_hisat2_idx.tar.gz unmapped_hisat2_idx
