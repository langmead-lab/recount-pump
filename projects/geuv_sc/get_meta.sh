#!/bin/bash

d=$(dirname $0)

STUDY=$(grep '^study' $d/project.ini | cut -d"=" -f2 | tr -d '[:space:]')

set -ex

get_metadata() {
    pushd $d/../../src
    python -m metadata.sradbv2 search "study.accession:ERP001942 OR study.accession:SRP066834" --gzip --output ${STUDY}.json
    popd
    mv $d/../../src/${STUDY}.json.gz $d/
}

get_metadata
