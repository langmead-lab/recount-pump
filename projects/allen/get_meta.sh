#!/bin/bash

d=$(dirname $0)

set -ex

study=allen
srp=SRP061902

get_metadata() {
    pushd $d/../../src
    python -m metadata.sradbv2 search "study_accession:${srp} AND experiment_library_strategy:\"rna seq\" AND experiment_library_source:transcriptomic AND experiment_platform:illumina" --gzip --output ${study}.json
    popd
    mv $d/../../src/${study}.json.gz $d/
}

get_metadata
