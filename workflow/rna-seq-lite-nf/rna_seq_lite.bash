#!/usr/bin/env bash

# Author: Ben Langmead
#  Email: langmea@cs.jhu.edu
#   Date: 1/5/2018

# Designed to run the nextflow script from inside a container where the
# supporting directories have already been set up, i.e.:
#  /recount-input
#  /recount-output
#  /recount-ref
#  /recount-temp

set -ex

NAME=rna_seq_lite

d=`dirname $0`

# Ensure directories
test -n "${INPUT}"
test -d "${INPUT}"
test -n "${OUTPUT}"
test -d "${OUTPUT}"
test -n "${RECOUNT_REF}"
test -d "${RECOUNT_REF}"
test -n "${RECOUNT_TEMP}"
test -d "${RECOUNT_TEMP}"

# Ensure tools are installed
which hisat2
which fastq-dump
which sambamba
which regtools
which nextflow

# Gather inputs
ls "${INPUT}"
INPUT_FILES=`ls ${INPUT}/*`
test -n "${INPUT_FILES}"

# Set cache directory for fastq-dump
mkdir -p "$HOME/.ncbi"
mkdir -p "${RECOUNT_TEMP}/ncbi"

cat >$HOME/.ncbi/user-settings.mkfg <<EOF
/repository/user/main/public/root = "${RECOUNT_TEMP}/ncbi"
EOF

mkdir -p ${RECOUNT_TEMP}/nextflow-temp

# Run nextflow workflow
export NXF_HOME=${RECOUNT_TEMP}/nextflow-temp && \
    $d/$NAME.nf \
        --in "${INPUT_FILES}" \
        --out "${OUTPUT}" \
        --ref "${RECOUNT_REF}" \
        --temp "${RECOUNT_TEMP}" $*

echo SUCCESS
