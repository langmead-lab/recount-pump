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

add_source() {
    url=$1
    python src/reference.py add-source $url 'NA' 'NA'  'NA' 'NA' 'NA' 'web'
}

srcid1=$(add_source "https://s3.amazonaws.com/recount-pump/ref/ce10/hisat2_idx.tar.gz" | tail -n 1)
srcid2=$(add_source "https://s3.amazonaws.com/recount-pump/ref/ce10/fasta.tar.gz" | tail -n 1)

python src/reference.py add-sources-to-set ${ssid} ${srcid1} ${ssid} ${srcid2}

# Annotation
#    tax_id = Column(Integer)  # refers to NCBI tax ids
#    url = Column(String(1024))
#    checksum = Column(String(32))
#    retrieval_method = Column(String(64))

asid=$(python src/reference.py add-annotation-set | tail -n 1)

add_annotation() {
    taxid=$1
    url=$2
    python src/reference.py add-annotation $taxid $url 'NA' 'web'
}

anid1=$(add_annotation ${TAXID} "https://s3.amazonaws.com/recount-pump/ref/ce10/gtf.tar.gz" | tail -n 1)

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



echo "++++++++++++++++++++++++++++++++++++++++++++++"
echo "        PHASE 3: Load input data"
echo "++++++++++++++++++++++++++++++++++++++++++++++"

echo "++++++++++++++++++++++++++++++++++++++++++++++"
echo "        PHASE 4: Set up project"
echo "++++++++++++++++++++++++++++++++++++++++++++++"

echo "++++++++++++++++++++++++++++++++++++++++++++++"
echo "        PHASE 5: Run project"
echo "++++++++++++++++++++++++++++++++++++++++++++++"
