#!/usr/bin/env bash

d=$(cd dirname $0 ; pwd)
pushd ${d}/../../src

set -ex

FN=hm_spike.txt
rm -f $d/${FN} ; touch $d/${FN}

url="https://raw.githubusercontent.com/nellore/rail/master/eval/GEUVADIS_28.manifest"
for srr in $(wget -q -O - ${url} | awk '{print $1}' | grep '^ftp' | awk -v FS='/' '{print $7}')
do
    python -m metadata.sradbv2 search "accession:${srr}"
    grep '"_id' search.json | sed 's/.*: "//' | sed 's/".*//' | sed 's/^/human_bulk_spike /' | tee -a $d/${FN}
done

python -m metadata.sradbv2 search-random-subset 'study.accession:SRP066834' 20
grep '"_id' search.json | sed 's/.*: "//' | sed 's/".*//' | sed 's/^/human_sc_spike /' | tee -a $d/${FN}

python -m metadata.sradbv2 search-random-subset 'study.accession:SRP006787' 20
grep '"_id' search.json | sed 's/.*: "//' | sed 's/".*//' | sed 's/^/mouse_bulk_spike /' | tee -a $d/${FN}

python -m metadata.sradbv2 search-random-subset 'study.accession:SRP131661' 20 --stop-after 1000
grep '"_id' search.json | sed 's/.*: "//' | sed 's/".*//' | sed 's/^/mouse_sc_spike /' | tee -a $d/${FN}

popd
