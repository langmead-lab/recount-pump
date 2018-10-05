#!/bin/bash

set -ex

which wget
STAGING=/tmp/staging

setup_refs() {
    manifest=$1
    test -f $manifest
    while IFS=, read -r src dst
    do
        fulldst=${STAGING}/${dst}
        mkdir -p $(dirname $fulldst)
        wget -O $fulldst $src
    done < $manifest
}

setup_metadata() {
    mkdir -p $STAGING/meta/ce10_test
    cd /tmp/src
    python -m metadata.sradbv2 search 'sample_taxon_id:6239 AND experiment_library_strategy:"rna seq" AND experiment_library_source:transcriptomic AND experiment_platform:illumina AND run_FileDate:["2017-01-01" TO "2017-05-01"]' --gzip --output $STAGING/meta/ce10_test/ce10_test.json
}

setup_metadata
setup_refs /tmp/manifest.csv

echo "Final contents:"
tree /tmp

