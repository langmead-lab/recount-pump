#!/bin/bash

STRATEGY='experiment.library_strategy:"rna seq"'
SOURCE='experiment.library_source:transcriptomic'
PLATFORM='experiment.platform:illumina'

# Note: dbGaP samples filtered out by default; to include, pass --include-dbgap to sradbv2

set -ex

for taxon in 9606 10090 ; do
    for tranche in 0 1 2 3 4 5 6 7 8 9 ; do
        FN="tranche_${tranche}_${taxon}.json"
        if [[ ! -f ${FN} ]] ; then
            pushd ../../src
            python -m metadata.sradbv2 \
            search \
                "${STRATEGY} AND ${SOURCE} AND ${PLATFORM} AND Status:live AND sample.taxon_id:${taxon} AND study.accession:*${tranche}"
            popd
            mv ../../src/search.json ${FN}
        fi
    done
done
