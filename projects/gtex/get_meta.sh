#!/bin/bash

d=$(dirname $0)

STUDY=$(grep '^study' $d/project.ini | cut -d"=" -f2 | tr -d '[:space:]')
SRP=$(grep '^srp' $d/project.ini | cut -d"=" -f2 | tr -d '[:space:]')

set -ex

test -n ${STUDY}
test -n ${SRP}

get_metadata() {
    pushd $d/../../src
    python -m metadata.sradbv2 search "study.accession:${SRP}" --gzip --output ${STUDY}.json
    popd
    mv $d/../../src/${STUDY}.json.gz $d/
}

get_metadata
