#!/bin/sh

set -ex

test -n "$(ls *.fna)"
test -f ../ercc/ercc_all.fasta

cat *.fna > virus.fa
cat virus.fa ../ercc/ercc_all.fasta > all.fa

OUTPUT=unmapped_hisat2_idx
rm -rf ${OUTPUT}
mkdir -p ${OUTPUT}

hisat2-build \
    --threads 8 \
    all.fa \
    ${OUTPUT}/genome

tar -zcvf unmapped_hisat2_idx.tar.gz unmapped_hisat2_idx
