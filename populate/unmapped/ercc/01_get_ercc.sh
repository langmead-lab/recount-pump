#!/bin/bash

# Concentrations URL:
CONC=https://tools.thermofisher.com/content/sfs/manuals/cms_095046.txt
[[ ! -f cms_095046.txt ]] && wget ${CONC}

# Sequences URL:
SEQ=https://tools.thermofisher.com/content/sfs/manuals/cms_095047.txt
[[ ! -f cms_095047.txt ]] && wget ${SEQ}
