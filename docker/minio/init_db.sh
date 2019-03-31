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
    mkdir -p $STAGING/recount-meta/ce10_test
    cd /tmp/src
    QUERY="sample_taxon_id:6239 AND"
    QUERY="${QUERY} experiment_library_strategy:\"rna seq\" AND"
    QUERY="${QUERY} experiment_library_source:transcriptomic AND"
    QUERY="${QUERY} experiment_platform:illumina AND"
    QUERY="${QUERY} run_bases:[1 TO 75000000] AND"
    QUERY="${QUERY} run_FileDate:[\"2013-01-01\" TO \"2017-05-01\"]"
    python -m metadata.sradbv2 search "${QUERY}" --gzip --output ${STAGING}/recount-meta/ce10_test/ce10_test.json
}

setup_metadata_stubbed() {
    # because sradbv2 changed and I haven't caught up yet, we have to
    # do this with a verbatim file for now

    # Got this list by doing:
    # aws --profile jhu-langmead s3 cp s3://recount-meta/ce10_test/ce10_small_test.json.gz - \
    #    | gzip -dc | grep '"_id"' | sed 's/.*: "//' | sed 's/".*//'
    mkdir -p $STAGING/recount-meta/ce10_test
    cat >> ${STAGING}/recount-meta/ce10_test/ce10_test.txt <<EOF
ce10test SRR4320662
ce10test SRR4320703
ce10test SRR4320751
ce10test SRR2054443
SIMULATION sim1 url https://recount-reads.s3.amazonaws.com/ce10/SRR5510884_1.fastq;https://recount-reads.s3.amazonaws.com/ce10/SRR5510884_2.fastq
EOF
    gzip -c ${STAGING}/recount-meta/ce10_test/ce10_test.txt > ${STAGING}/recount-meta/ce10_test/ce10_test.txt.gz
    rm -f ${STAGING}/recount-meta/ce10_test/ce10_test.txt
}

setup_manifest /tmp/manifest.csv
#setup_metadata
setup_metadata_stubbed

rm -rf /tmp/src

echo "Final contents:"
tree /tmp
