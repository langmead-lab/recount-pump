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
test -n "${RECOUNT_CPUS}"

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

# Run nextflow workflow
if [[ -f /workflow.nf ]] ; then
    mkdir -p ${RECOUNT_TEMP}/nextflow-home ${RECOUNT_TEMP}/nextflow-temp
    chmod -R a+rwx ${RECOUNT_TEMP}/nextflow-home ${RECOUNT_TEMP}/nextflow-temp
    echo "executor.\$local.cpus = ${RECOUNT_CPUS}" > ${RECOUNT_TEMP}/.nx.cfg
    export NXF_TEMP=${RECOUNT_TEMP}/nextflow-temp && \
        nextflow /workflow.nf \
            -C ${RECOUNT_TEMP}/.nx.cfg \
            --in "${INPUT_FILES}" \
            --out "${RECOUNT_OUTPUT}" \
            --ref "${RECOUNT_REF}" \
            --temp "${RECOUNT_TEMP}" \
            --cpus "${RECOUNT_CPUS}" \
            $*
elif [[ -f /Snakefile ]] ; then
    snakemake --snakefile /Snakefile --config \
        input="${INPUT_FILES}" \
        output="${RECOUNT_OUTPUT}" \
        ref="${RECOUNT_REF}" \
        temp="${RECOUNT_TEMP}" \
        cpus="${RECOUNT_CPUS}" \
        $*
else
    echo "Could not detect workflow script"
    exit 1
fi

# These will need to be removed outside the container, where we might
# not want to have to be root to clean up
chmod -R a+rwx ${RECOUNT_OUTPUT} ${RECOUNT_TEMP}

echo SUCCESS
