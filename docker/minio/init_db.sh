#!/bin/bash

set -ex

which curl
STAGING=/tmp/staging

setup_manifest() {
    manifest=$1
    test -f $manifest
    while IFS=, read -r src dst
    do
        fulldst=${STAGING}/${dst}
        mkdir -p $(dirname $fulldst)
        curl -L -o $fulldst $src
    done < $manifest
}

setup_metadata() {
    mkdir -p $STAGING/meta/ce10_test
    cd /tmp/src
    QUERY="sample_taxon_id:6239 AND"
    QUERY="${QUERY} experiment_library_strategy:\"rna seq\" AND"
    QUERY="${QUERY} experiment_library_source:transcriptomic AND"
    QUERY="${QUERY} experiment_platform:illumina AND"
    QUERY="${QUERY} run_bases:[1 TO 75000000] AND"
    QUERY="${QUERY} run_FileDate:[\"2013-01-01\" TO \"2017-05-01\"]"
    python -m metadata.sradbv2 search "${QUERY}" --gzip --output $STAGING/meta/ce10_test/ce10_test.json
}

setup_manifest /tmp/manifest.csv

echo "Final contents:"
tree /tmp

