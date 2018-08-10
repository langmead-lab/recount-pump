#!/usr/bin/env bash

# Author: Ben Langmead
#  Email: langmea@cs.jhu.edu
#   Date: 1/5/2018

# Designed to run the nextflow script from inside a container, where relevant
# directories are indicated by environment variables RECOUNT_INPUT,
# RECOUNT_OUTPUT, RECOUNT_REF, RECOUNT_TEMP

set -ex

# Ensure directories
test -n "${RECOUNT_INPUT}"
test -d "${RECOUNT_INPUT}"
test -n "${RECOUNT_OUTPUT}"
test -d "${RECOUNT_OUTPUT}"
test -n "${RECOUNT_REF}"
test -d "${RECOUNT_REF}"
test -n "${RECOUNT_TEMP}"
test -d "${RECOUNT_TEMP}"

# Gather inputs
ls "${RECOUNT_INPUT}"
INPUT_FILES=`ls ${RECOUNT_INPUT}/*`
test -n "${INPUT_FILES}"

# Set cache directory for fastq-dump
mkdir -p "$HOME/.ncbi"
mkdir -p "${RECOUNT_TEMP}/ncbi"

cat >$HOME/.ncbi/user-settings.mkfg <<EOF
/repository/user/main/public/root = "${RECOUNT_TEMP}/ncbi"
EOF

mkdir -p ${RECOUNT_TEMP}/nextflow-home ${RECOUNT_TEMP}/nextflow-temp
chmod -R a+rwx ${RECOUNT_TEMP}/nextflow-home ${RECOUNT_TEMP}/nextflow-temp

# Run nextflow workflow
export NXF_TEMP=${RECOUNT_TEMP}/nextflow-temp && /workflow.nf \
    --in "${INPUT_FILES}" \
    --out "${RECOUNT_OUTPUT}" \
    --ref "${RECOUNT_REF}" \
    --temp "${RECOUNT_TEMP}" $*

chmod -R a+rwx ${RECOUNT_OUTPUT}

echo SUCCESS
