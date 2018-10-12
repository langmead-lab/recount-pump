#!/bin/bash

d=$(dirname $0)

set -ex

get_metadata() {
    pushd $d/../../src
    python -m metadata.sradbv2 search "study_accession:ERP001942" --gzip --output geuv.json
    popd
    mv $d/../../src/geuv.json.gz $d/
}

get_metadata
