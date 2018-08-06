#!/usr/bin/env bash

# Author: Ben Langmead <ben.langmead@gmail.com>
# License: MIT

#
# Assuming that:
# 1. Minio is serving on port 29000
# 2. Postgres is serving on port 25432
# 3. Rmq is serving on port 25672
# 4. Image files are being served at a local directory defined by
#    $RECOUNT_IMAGES
#
#
# Prereqs:
#
# === ~/.recount/db.ini ===
# [client]
# url=postgres://recount:recount-postgres@127.0.0.1:25432/recount-test
# password=recount-postgres
# host=127.0.0.1
# port=25432
# user=recount
#
# === ~/.recount/queue.ini ===
# [queue]
# type=rmq
# host=localhost
# port=25672
#
# Optional:
#
# If you want to use a log aggregator:
#
# === ~/.recount/log.ini ===
# [syslog]
# host = XXXX.YYYY.com
# port = XXXXX
# format = %(asctime)s %(hostname)s recount-pump: %(message)s
# datefmt = %b %d %H:%M:%S 
# [watchtower]
# log_group = watchtower
# stream_name = recount-pump
#

set -ex

TAXID=6239
RUN_NAME=ce10_test
ANALYSIS_DIR=$PWD/analyses
mkdir -p ${ANALYSIS_DIR}

RNA_SEQ_LITE="quay.io_benlangmead_recount-rna-seq-lite-nf-2018-07-23-353aacc3b34f.img"

[ -z "${RECOUNT_IMAGES}" ] && \
    echo "Must set RECOUNT_IMAGES first" && exit 1
[ ! -d "${RECOUNT_IMAGES}" ] && \
    echo "Directory \"${RECOUNT_IMAGES}\" does not exist" && exit 1
[ ! -f "${RECOUNT_IMAGES}/${RNA_SEQ_LITE}" ] && \
    echo "File \"${RECOUNT_IMAGES}/${RNA_SEQ_LITE}\" does not exist" && exit 1

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

ssid=$(python src/reference.py add-source-set | tail -n 1)

add_source() (
    set -exo pipefail
    url=$1
    python src/reference.py add-source $url 'NA' 'NA'  'NA' 'NA' 'NA' 'web' | tail -n 1
)

srcid1=$(add_source "https://s3.amazonaws.com/recount-pump/ref/ce10/hisat2_idx.tar.gz")
srcid2=$(add_source "https://s3.amazonaws.com/recount-pump/ref/ce10/fasta.tar.gz")

python src/reference.py add-sources-to-set ${ssid} ${srcid1} ${ssid} ${srcid2}

# Annotation
#    tax_id = Column(Integer)  # refers to NCBI tax ids
#    url = Column(String(1024))
#    checksum = Column(String(32))
#    retrieval_method = Column(String(64))

asid=$(python src/reference.py add-annotation-set | tail -n 1)

add_annotation() (
    set -exo pipefail
    taxid=$1
    url=$2
    python src/reference.py add-annotation $taxid $url 'NA' 'web' | tail -n 1
)

anid1=$(add_annotation ${TAXID} "https://s3.amazonaws.com/recount-pump/ref/ce10/gtf.tar.gz")

python src/reference.py add-annotations-to-set ${asid} ${anid1}

# Reference
#   tax_id = Column(Integer)  # refers to NCBI tax ids
#   name = Column(String(64))  # assembly name, like GRCh38, etc
#   longname = Column(String(256))  # assembly name, like GRCh38, etc
#   conventions = Column(String(256))  # info about naming conventions, e.g. "chr"
#   comment = Column(String(256))
#   source_set = Column(Integer, ForeignKey('source_set.id'))
#   annotation_set = Column(Integer, ForeignKey('annotation_set.id'))

python src/reference.py \
    add-reference \
    ${TAXID} \
    ce10 \
    caenorhabditis_elegans \
    "" \
    "end-to-end test" \
    ${ssid} \
    ${asid}

echo "++++++++++++++++++++++++++++++++++++++++++++++"
echo "        PHASE 2: Load analysis data"
echo "++++++++++++++++++++++++++++++++++++++++++++++"

# Cluster
#    name = Column(String(1024))  # "marcc" or "stampede2" for now
#    cluster_analysis = relationship("ClusterAnalysis")

# Analysis
#    name = Column(String(1024))
#    image_url = Column(String(4096))
#    cluster_analysis = relationship("ClusterAnalysis")

# ClusterAnalysis
#    analysis_id = Column(Integer, ForeignKey('analysis.id'))
#    cluster_id = Column(Integer, ForeignKey('cluster.id'))
#    wrapper_url = Column(String(4096))  # image wrapper

add_analysis_ex() (
    set -exo pipefail
    name=$1
    image_url=$2
    cluster_name_wrapper_url_pairs=$3
    python src/analysis.py add-analysis-ex ${name} ${image_url} ${cluster_name_wrapper_url_pairs} | tail -n 1
)

# TODO: need to consider what to do about wrappers

rna_seq_lite_id=$(add_analysis_ex rna_seq_lite "${RECOUNT_IMAGES}/${RNA_SEQ_LITE}" "default ${RECOUNT_IMAGES}/rna_seq_lite_default.bash")

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

add_input_set() (
    set -exo pipefail
    name=$1
    python src/input.py add-input-set ${name} | tail -n 1
)

isid=$(add_input_set "ce10_rna_seq")

add_input() (
    set -exo pipefail
    acc_r=$1
    acc_s=$2
    url_1=$3
    retrieval_method=$4
    python src/input.py add-input ${acc_r} ${acc_s} ${url_1} NA NA NA NA NA ${retrieval_method} | tail -n 1
)

# TODO: get these from SRAv2 JSON instead of hard-coding them here
in1=$(add_input SRR5510884 SRP106481 ce10 s3)
in2=$(add_input SRR5510089 SRP106481 ce10 s3)
in3=$(add_input SRR5509792 SRP106481 ce10 s3)
in4=$(add_input SRR2054434 SRP000401 ce10 s3)
in5=$(add_input SRR2054439 SRP000401 ce10 s3)
in6=$(add_input SRR578035 SRP000401 ce10 s3)
in7=$(add_input SRR3170393 SRP070155 ce10 s3)
in8=$(add_input SRR1557855 SRP045778 ce10 s3)

python src/input.py add-inputs-to-set \
    ${isid} ${in1} ${isid} ${in2} ${isid} ${in3} \
    ${isid} ${in4} ${isid} ${in5} ${isid} ${in6} \
    ${isid} ${in7} ${isid} ${in8} | tail -n 1

echo "++++++++++++++++++++++++++++++++++++++++++++++"
echo "        PHASE 4: Set up project"
echo "++++++++++++++++++++++++++++++++++++++++++++++"

# Project
#    name = Column(String(1024))
#    input_set_id = Column(Integer, ForeignKey('input_set.id'))
#    analysis_id = Column(Integer, ForeignKey('analysis.id'))

add_project() (
    set -exo pipefail
    name=$1
    input_set_id=$2
    analysis_id=$3
    python src/pump.py add-project ${name} ${analysis_id} ${input_set_id} | tail -n 1
)

proj_id=$(add_project project2 ${isid} ${rna_seq_lite_id})

echo "++++++++++++++++++++++++++++++++++++++++++++++"
echo "        PHASE 5: Summarize project"
echo "++++++++++++++++++++++++++++++++++++++++++++++"

# Print out helpful info about the project and its various components

python src/pump.py summarize-project ${proj_id}

echo "++++++++++++++++++++++++++++++++++++++++++++++"
echo "        PHASE 6: Stage project"
echo "++++++++++++++++++++++++++++++++++++++++++++++"

python src/pump.py stage ${proj_id}

echo "++++++++++++++++++++++++++++++++++++++++++++++"
echo "        PHASE 7: Prepare project"
echo "++++++++++++++++++++++++++++++++++++++++++++++"

cat >cluster.ini <<EOF
[cluster]
name = ${RUN_NAME}
analysis_dir = ${ANALYSIS_DIR}
EOF

python src/job_loop.py \
    prepare ${proj_id} \
    --cluster-ini cluster.ini

echo "++++++++++++++++++++++++++++++++++++++++++++++"
echo "        PHASE 8: Run project"
echo "++++++++++++++++++++++++++++++++++++++++++++++"

python src/job_loop.py run \
    ${proj_id} \
    --cluster-ini cluster.ini \
    --max-fail 3 \
    --poll-seconds 1
