#!/bin/bash

d=$(dirname $0)

set -ex

study=tair10araport11

get_metadata() {
    pushd $d/../../src
    
    QUERY="sample_taxon_id:3702"
    QUERY="${QUERY} AND experiment_library_strategy:\"rna seq\""
    QUERY="${QUERY} AND experiment_library_source:transcriptomic"
    QUERY="${QUERY} AND experiment_platform:illumina"
    
    if false ; then
        QUERY="${QUERY} AND (study_abstract:\"single-cell\" OR experiment_library_construction_protocol:\"single-cell\" OR study_title:\"single-cell\")"
    fi
    
    python -m metadata.sradbv2 search "${QUERY}" --gzip --output ${study}.json
    popd
    mv $d/../../src/${study}.json.gz $d/
}

get_metadata
