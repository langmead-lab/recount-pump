#!/usr/bin/env bash

set -ex

python -m metadata.sradbv2 search-random-subset 'sample.taxon_id:9606 AND experiment.library_strategy:"rna seq" AND experiment.library_source:transcriptomic AND experiment.platform:illumina AND NOT (study.abstract:"single-cell" OR experiment.library_construction_protocol:"single-cell" OR study.title:"single-cell")' 1000 --stop-after=50000 --output bulk.json

python -m metadata.sradbv2 search-random-subset 'sample.taxon_id:9606 AND experiment.library_strategy:"rna seq" AND experiment.library_source:transcriptomic AND experiment.platform:illumina AND (study.abstract:"single-cell" OR experiment.library_construction_protocol:"single-cell" OR study.title:"single-cell")' 1000 --stop-after=50000 --output sc.json

head -n -1 sc.json > sc.cut.json
tail -n +2 bulk.json > bulk.cut.json
cat sc.cut.json > h2k.json
echo "},{" >> h2k.json
cat bulk.cut.json >> h2k.json
gzip h2k.json
