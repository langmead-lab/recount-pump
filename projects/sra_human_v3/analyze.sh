#!/bin/sh

for taxon in 9606 10090 ; do
    pypy analyze.py tranche_?_${taxon}.json > summ_${taxon}.csv
done

