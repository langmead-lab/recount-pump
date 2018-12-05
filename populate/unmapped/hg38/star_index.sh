#!/bin/sh

cat *.fna > virus.fa

OUTPUT=unmapped_star_idx
TEMP=unmapped_star_idx.temp
rm -rf ${OUTPUT} ${TEMP}
mkdir -p ${OUTPUT}

STAR \
    --runThreadN 8 \
    --runMode genomeGenerate \
    --genomeDir ${OUTPUT} \
    --outTmpDir ${TEMP} \
    --genomeFastaFiles virus.fa
