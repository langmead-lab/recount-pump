#!/bin/bash

# Concentrations URL:
CONC=https://assets.thermofisher.com/TFS-Assets/LSG/manuals/cms_095046.txt
wget --unlink -O cms_095046.txt ${CONC}

# Sequences URL:
SEQ=https://assets.thermofisher.com/TFS-Assets/LSG/manuals/ERCC92.zip
wget --unlink -O ERCC92.zip ${SEQ}
unzip -o ERCC92.zip
ln -fs ERCC92.fa ercc_all.fasta
ln -fs ERCC92.gtf ercc_all.gtf
