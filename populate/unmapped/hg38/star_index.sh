#!/bin/sh

cat *.fna > virus.fa

OUTPUT=star_unmapped_idx
TEMP=star_unmapped_idx.temp
rm -rf ${OUTPUT} ${TEMP}
mkdir -p ${OUTPUT}

STAR \
    --runThreadN 8 \
    --runMode genomeGenerate \
    --genomeDir ${OUTPUT} \
    --outTmpDir ${TEMP} \
    --genomeFastaFiles virus.fa
