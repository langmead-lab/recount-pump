#!/bin/sh

set -ex

test -f ../ercc/ercc_all.fasta
test -f ../sirv/SIRV_isoforms_multi-fasta_170612a.fasta

cat  ../ercc/ercc_all.fasta ../sirv/SIRV_isoforms_multi-fasta_170612a.fasta > all.fa

OUTPUT=unmapped_hisat2_idx
rm -rf ${OUTPUT}
mkdir -p ${OUTPUT}

hisat2-build \
    --threads 8 \
    all.fa \
    ${OUTPUT}/genome

tar -zcvf unmapped_hisat2_idx.tar.gz unmapped_hisat2_idx
