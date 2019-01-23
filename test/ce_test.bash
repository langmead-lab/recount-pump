#!/usr/bin/env bash

# Author: Ben Langmead <ben.langmead@gmail.com>
# License: MIT

set -ex

d=$(dirname $0)
test -n "${RECOUNT_CREDS}"

TAXID=6239
WORKFLOW=rs5
IMAGE=$(cat $d/../workflow/$WORKFLOW/image.txt)
IMAGE_VER=$(cat $d/../workflow/$WORKFLOW/ver.txt)
ANA_URL="docker://${IMAGE}:${IMAGE_VER}"
SRC_DIR="src"
ARGS="--ini-base ${RECOUNT_CREDS}"
OUTPUT_DIR=$(grep '^output_base' ${RECOUNT_CREDS}/cluster.ini | cut -d"=" -f2 | tr -d '[:space:]')
SPECIES=ce10
STUDY=ce10_test

mc stat s3/recount-meta
mc stat s3/recount-ref
! mc stat s3/recount-output && mc mb s3/recount-output
mc stat s3/recount-output

input_url='s3://recount-meta/ce10_test/ce10_small_test.json.gz'

echo "++++++++++++++++++++++++++++++++++++++++++++++"
echo "        PHASE 1: Load reference data"
echo "++++++++++++++++++++++++++++++++++++++++++++++"

# Source:
#    url_1 = Column(String(1024))  # URL where obtained
#    url_2 = Column(String(1024))  # URL where obtained
#    url_3 = Column(String(1024))  # URL where obtained
#    checksum_1 = Column(String(256))
#    checksum_2 = Column(String(256))
#    checksum_3 = Column(String(256))
#    retrieval_method = Column(String(64))

ssid=$(python ${SRC_DIR}/reference.py ${ARGS} add-source-set | tail -n 1)
test -n "${ssid}"

add_source() (
    set -exo pipefail
    url=$1
    retrieval_method=$2
    python ${SRC_DIR}/reference.py ${ARGS} \
        add-source "${url}" 'NA' 'NA' 'NA' 'NA' 'NA' "${retrieval_method}" | tail -n 1
)

srcid1=$(add_source "s3://recount-ref/${SPECIES}/star_idx.tar.gz" 's3')
srcid2=$(add_source "s3://recount-ref/${SPECIES}/fasta.tar.gz" 's3')
test -n "${srcid1}"
test -n "${srcid2}"

python ${SRC_DIR}/reference.py ${ARGS} \
    add-sources-to-set ${ssid} ${srcid1} ${ssid} ${srcid2}

# Annotation
#    tax_id = Column(Integer)  # refers to NCBI tax ids
#    url = Column(String(1024))
#    checksum = Column(String(32))
#    retrieval_method = Column(String(64))

asid=$(python ${SRC_DIR}/reference.py ${ARGS} add-annotation-set | tail -n 1)
test -n "${asid}"

add_annotation() (
    set -exo pipefail
    taxid=$1
    url=$2
    retrieval_method=$3
    python ${SRC_DIR}/reference.py ${ARGS} \
        add-annotation "${taxid}" "${url}" 'NA' "${retrieval_method}" | tail -n 1
)

anid1=$(add_annotation ${TAXID} "s3://recount-ref/${SPECIES}/gtf.tar.gz" 's3')
test -n "${anid1}"

python ${SRC_DIR}/reference.py ${ARGS} \
    add-annotations-to-set ${asid} ${anid1}

# Reference
#   tax_id = Column(Integer)  # refers to NCBI tax ids
#   name = Column(String(64))  # assembly name, like GRCh38, etc
#   longname = Column(String(256))  # assembly name, like GRCh38, etc
#   conventions = Column(String(256))  # info about naming conventions, e.g. "chr"
#   comment = Column(String(256))
#   source_set = Column(Integer, ForeignKey('source_set.id'))
#   annotation_set = Column(Integer, ForeignKey('annotation_set.id'))

add_reference() (
    taxid=$1
    shortname=$2
    longname=$3
    source_set_id=$4
    annotation_set_id=$5
    python ${SRC_DIR}/reference.py ${ARGS} \
        add-reference "${taxid}" "${shortname}" "${longname}" 'NA' 'NA' \
                      "${source_set_id}" "${annotation_set_id}" | tail -n 1
)

ref_id=$(add_reference ${TAXID} "${SPECIES}" 'caenorhabditis_elegans' ${ssid} ${asid})
test -n "${ref_id}"

echo "++++++++++++++++++++++++++++++++++++++++++++++"
echo "        PHASE 2: Load analysis data"
echo "++++++++++++++++++++++++++++++++++++++++++++++"

# Analysis
#    name = Column(String(1024))
#    image_url = Column(String(4096))

add_analysis() (
    set -exo pipefail
    name=$1
    image_url=$2
    config=$3
    python ${SRC_DIR}/analysis.py ${ARGS} \
        add-analysis ${name} ${image_url} ${config} | tail -n 1
)

cat >/tmp/.ce_test.config.json <<EOF
{
    "star": "--alignIntronMax 20000"
}
EOF

rs1_id=$(add_analysis rs1 "${ANA_URL}" file:///tmp/.ce_test.config.json)
test -n "${rs1_id}"

echo "++++++++++++++++++++++++++++++++++++++++++++++"
echo "        PHASE 3: Load input data"
echo "++++++++++++++++++++++++++++++++++++++++++++++"

# Input
#    acc_r = Column(String(64))        # run accession
#    acc_s = Column(String(64))        # study accession
#    url_1 = Column(String(1024))      # URL for sample, or for just mate 1
#    url_2 = Column(String(1024))      # URL for mate 2
#    url_3 = Column(String(1024))      # unlikely to be used; maybe for barcode?
#    checksum_1 = Column(String(256))  # checksum for file at url_1
#    checksum_2 = Column(String(256))  # checksum for file at url_2
#    checksum_3 = Column(String(256))  # checksum for file at url_3
#    retrieval_method = Column(String(64))  # suggested retrieval method

# InputSet
#    name = Column(String(1024))
#    inputs = relationship("Input", secondary=input_association_table)

input_fn=$(basename ${input_url})

python ${SRC_DIR}/mover.py ${ARGS} get "${input_url}" "${input_fn}"

[[ ! -f ${input_fn} ]] && echo "Could not get input json" && exit 1 

import_input_set() (
    set -exo pipefail
    json_file=$1
    input_set_name=$2
    limit=$3
    python ${SRC_DIR}/input.py ${ARGS} import-json \
        --limit "${limit}" \
        "${json_file}" "${input_set_name}" | tail -n 1   
)

isid=$(import_input_set "${input_fn}" 'ce10_rna_seq' 3)
test -n "${isid}"

rm -f ${input_fn}

echo "++++++++++++++++++++++++++++++++++++++++++++++"
echo "        PHASE 4: Set up project"
echo "++++++++++++++++++++++++++++++++++++++++++++++"

# Project
#    name = Column(String(1024))
#    input_set_id = Column(Integer, ForeignKey('input_set.id'))
#    analysis_id = Column(Integer, ForeignKey('analysis.id'))
#    reference_id = Column(Integer, ForeignKey('reference.id'))

add_project() (
    set -exo pipefail
    name=$1
    input_set_id=$2
    analysis_id=$3
    reference_id=$4
    python ${SRC_DIR}/pump.py ${ARGS} \
        add-project ${name} ${analysis_id} ${input_set_id} ${reference_id} | tail -n 1
)

proj_id=$(add_project "${STUDY}" ${isid} ${rs1_id} ${ref_id})
test -n "${proj_id}"

echo "++++++++++++++++++++++++++++++++++++++++++++++"
echo "        PHASE 5: Summarize project"
echo "++++++++++++++++++++++++++++++++++++++++++++++"

python ${SRC_DIR}/pump.py ${ARGS} summarize-project ${proj_id}

echo "++++++++++++++++++++++++++++++++++++++++++++++"
echo "        PHASE 6: Stage project"
echo "++++++++++++++++++++++++++++++++++++++++++++++"

python ${SRC_DIR}/pump.py ${ARGS} stage ${proj_id}

echo "++++++++++++++++++++++++++++++++++++++++++++++"
echo "        PHASE 7: Prepare project"
echo "++++++++++++++++++++++++++++++++++++++++++++++"

python ${SRC_DIR}/cluster.py ${ARGS} \
    prepare ${proj_id}

echo "++++++++++++++++++++++++++++++++++++++++++++++"
echo "        PHASE 9: Run project"
echo "++++++++++++++++++++++++++++++++++++++++++++++"

python ${SRC_DIR}/cluster.py ${ARGS} \
    run ${proj_id} \
    --max-fail 3 \
    --poll-seconds 1 \
    --sysmon-interval 5

echo "++++++++++++++++++++++++++++++++++++++++++++++"
echo "        PHASE 10: Print schema"
echo "++++++++++++++++++++++++++++++++++++++++++++++"

python ${SRC_DIR}/schema_graph.py ${ARGS} \
    --prefix ${OUTPUT_DIR}/ce10_test plot

echo "++++++++++++++++++++++++++++++++++++++++++++++"
echo "        PHASE 11: Copy output back"
echo "++++++++++++++++++++++++++++++++++++++++++++++"

mkdir -p ${OUTPUT_DIR}/s3_output
mc mirror s3/recount-output ${OUTPUT_DIR}/s3_output
