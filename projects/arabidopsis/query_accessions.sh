#!/usr/bin/env bash

set -ex

d=$(dirname $0)
d=$(cd ${d} ; pwd)

echo "Initial dir: ${d}"

out_fn=$d/search.json
rm -f ${out_fn} ; touch ${out_fn}

BATCH_SZ=100

pushd ${d}/../../src

do_query() {
    python -m metadata.sradbv2 search "$1"
    cat search.json >> ${out_fn}
}

n=0
accs=""
for acc in $(cat ${d}/Col-0_OnlyAccessionList.txt) ; do
    if [[ -z "${accs}" ]] ; then
        accs="accession:${acc}"
    else
        accs="${accs} OR accession:${acc}"
    fi
    ((n++))
    if [[ ${n} == ${BATCH_SZ} ]] ; then
        do_query "${accs}"
        n=0
        accs=""
    fi
done

if [[ -n "${accs}" ]] ; then
    do_query "${accs}"
fi

popd
