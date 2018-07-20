#!/usr/bin/env bash

#
# Assuming that the minio, postgres and rmq are running and serving on
# their special ports
#
# rmq: 25672
# postgres: 25432
# minio: 29000
#

set -ex

TAXID=6239

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

ANALYSIS_URL='s3://recount-pump/image/'
RNA_SEQ="quay.io_benlangmead_recount-rna-seq-nf-2018-07-19-e549a6d2c1e8.img.gz"
RNA_SEQ_LITE="quay.io_benlangmead_recount-rna-seq-lite-nf-2018-07-19-efb005fb600f.img.gz"

rna_seq_id=$(add_analysis_ex rna_seq "${ANALYSIS_URL}/${RNA_SEQ}" "default ${ANALYSIS_URL}/rna_seq_lite.bash")
rna_seq_lite_id=$(add_analysis_ex rna_seq_lite "${ANALYSIS_URL}/${RNA_SEQ_LITE}" "default ${ANALYSIS_URL}/rna_seq_lite_default.bash")

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

proj_id1=$(add_project project1 ${isid} ${rna_seq_id})
proj_id2=$(add_project project1 ${isid} ${rna_seq_lite_id})

echo "++++++++++++++++++++++++++++++++++++++++++++++"
echo "        PHASE 5: Summarize project"
echo "++++++++++++++++++++++++++++++++++++++++++++++"

# Print out helpful info about the project and its various components

# TODO: implement this
python src/pump.py summarize-project ${proj_id1} | tail -n 1

python src/pump.py summarize-project ${proj_id2} | tail -n 1

echo "++++++++++++++++++++++++++++++++++++++++++++++"
echo "        PHASE 6: Run project"
echo "++++++++++++++++++++++++++++++++++++++++++++++"
