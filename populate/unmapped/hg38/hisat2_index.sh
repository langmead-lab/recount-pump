#!/bin/sh

cat *.fna > virus.fa

OUTPUT=unmapped_hisat2_idx
rm -rf ${OUTPUT}
mkdir -p ${OUTPUT}

hisat2-build \
    --threads 8 \
    virus.fa \
    ${OUTPUT}/genome
