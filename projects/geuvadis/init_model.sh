#!/usr/bin/env bash

# Author: Ben Langmead <ben.langmead@gmail.com>
# License: MIT

d=$(dirname $0)

set -ex

TAXID=9606
RS1="docker://quay.io/benlangmead/recount-rs2:0.1.6"
DB_INI="--db-ini ${d}/ini/db.ini.override"
Q_INI="--queue-ini ${d}/ini/queue.ini.override"
S3_INI="--s3-ini ${d}/ini/s3.ini.override"
LOG_INI="--log-ini ${d}/ini/log.ini.override"
SRC_DIR="$d/../../src"
ARGS="${LOG_INI}"

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

ssid=$(python ${SRC_DIR}/reference.py ${ARGS} ${DB_INI} add-source-set | tail -n 1)
test -n "${ssid}"

add_source() (
    set -exo pipefail
    url=$1
    retrieval_method=$2
    python ${SRC_DIR}/reference.py ${ARGS} ${DB_INI} \
        add-source "${url}" 'NA' 'NA' 'NA' 'NA' 'NA' "${retrieval_method}" | tail -n 1
)

srcid1=$(add_source 's3://recount-ref/hg38/hisat2_idx.tar.gz' 's3')
srcid2=$(add_source 's3://recount-ref/hg38/fasta.tar.gz' 's3')
test -n "${srcid1}"
test -n "${srcid2}"

python ${SRC_DIR}/reference.py ${ARGS} ${DB_INI} \
    add-sources-to-set ${ssid} ${srcid1} ${ssid} ${srcid2}

# Annotation
#    tax_id = Column(Integer)  # refers to NCBI tax ids
#    url = Column(String(1024))
#    checksum = Column(String(32))
#    retrieval_method = Column(String(64))

asid=$(python ${SRC_DIR}/reference.py ${ARGS} ${DB_INI} add-annotation-set | tail -n 1)
test -n "${asid}"

add_annotation() (
    set -exo pipefail
    taxid=$1
    url=$2
    retrieval_method=$3
    python ${SRC_DIR}/reference.py ${ARGS} ${DB_INI} \
        add-annotation "${taxid}" "${url}" 'NA' "${retrieval_method}" | tail -n 1
)

anid1=$(add_annotation ${TAXID} 's3://recount-ref/hg38/gtf.tar.gz' 's3')
test -n "${anid1}"

python ${SRC_DIR}/reference.py ${ARGS} ${DB_INI} \
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
    python ${SRC_DIR}/reference.py ${ARGS} ${DB_INI} \
        add-reference "${taxid}" "${shortname}" "${longname}" 'NA' 'NA' \
                      "${source_set_id}" "${annotation_set_id}" | tail -n 1
)

ref_id=$(add_reference ${TAXID} 'hg38' 'homo_sapiens' ${ssid} ${asid})
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
    python ${SRC_DIR}/analysis.py ${ARGS} ${DB_INI} \
        add-analysis ${name} ${image_url} | tail -n 1
)

rs1id=$(add_analysis rs1_0_1_2 "${RS1}")
test -n "${rs1id}"

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

input_url='s3://recount-pump-experiments/geuv/geuv.json.gz'
input_fn=$(basename ${input_url})
rm -f "/tmp/${input_fn}"

python ${SRC_DIR}/mover.py ${ARGS} ${S3_INI} get "${input_url}" "/tmp/${input_fn}"

[ ! -f "/tmp/${input_fn}" ] && echo "Could not get input json" && exit 1 

import_input_set() (
    set -exo pipefail
    json_file=$1
    input_set_name=$2
    python ${SRC_DIR}/input.py ${ARGS} ${DB_INI} import-json \
        "${json_file}" "${input_set_name}" | tail -n 1   
)

isid=$(import_input_set "/tmp/${input_fn}" 'geuvadis_ERP001942')
test -n "${isid}"
rm -f "/tmp/${input_fn}"

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
    python ${SRC_DIR}/pump.py ${ARGS} ${DB_INI} \
        add-project ${name} ${analysis_id} ${input_set_id} ${reference_id} | tail -n 1
)

proj_id=$(add_project 'geuvadis-project' ${isid} ${rs1id} ${ref_id})
test -n "${proj_id}"

echo "++++++++++++++++++++++++++++++++++++++++++++++"
echo "        PHASE 5: Summarize project"
echo "++++++++++++++++++++++++++++++++++++++++++++++"

python ${SRC_DIR}/pump.py ${ARGS} ${DB_INI} summarize-project ${proj_id}

echo "++++++++++++++++++++++++++++++++++++++++++++++"
echo "        PHASE 6: Stage project"
echo "++++++++++++++++++++++++++++++++++++++++++++++"

python ${SRC_DIR}/pump.py ${ARGS} ${DB_INI} ${Q_INI} stage ${proj_id}