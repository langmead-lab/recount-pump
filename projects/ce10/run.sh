#!/usr/bin/env bash

set -ex

d=$(dirname $0)

ln -s -f cluster-fake.ini creds/cluster.ini

ARGS="--ini-base creds"
SRC_DIR="${d}/../../src"
PROJ_INI=$1
if [[ -z "${PROJ_INI}" ]] ; then
    PROJ_INI=project.ini
fi
STUDY=$(grep '^study' ${PROJ_INI} | cut -d"=" -f2 | tr -d '[:space:]')
OUTPUT_DIR=$(grep '^output_base' creds/cluster.ini | cut -d"=" -f2 | tr -d '[:space:]')
mkdir -p "${OUTPUT_DIR}"

mc mb --ignore-existing s3/recount-output

echo "++++++++++++++++++++++++++++++++++++++++++++++"
echo "        PHASE 7: Prepare project"
echo "++++++++++++++++++++++++++++++++++++++++++++++"

python ${SRC_DIR}/cluster.py ${ARGS} prepare ${STUDY}

echo "++++++++++++++++++++++++++++++++++++++++++++++"
echo "        PHASE 9: Run project"
echo "++++++++++++++++++++++++++++++++++++++++++++++"

python ${SRC_DIR}/cluster.py ${ARGS} \
    run ${STUDY} \
    --max-fail 3 \
    --poll-seconds 1 \
    --sysmon-interval 5

echo "++++++++++++++++++++++++++++++++++++++++++++++"
echo "        PHASE 10: Print schema"
echo "++++++++++++++++++++++++++++++++++++++++++++++"

python ${SRC_DIR}/schema_graph.py ${ARGS} --prefix ${OUTPUT_DIR}/ce10_test plot

echo "++++++++++++++++++++++++++++++++++++++++++++++"
echo "        PHASE 11: Copy output back"
echo "++++++++++++++++++++++++++++++++++++++++++++++"

mkdir -p ${OUTPUT_DIR}/s3_output
mc mirror --overwrite s3/recount-output ${OUTPUT_DIR}/s3_output
