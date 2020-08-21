#!/usr/bin/env bash

# Author: Ben Langmead
#  Email: langmea@cs.jhu.edu
#   Date: 1/5/2018

# Designed to run the nextflow script from inside a container, where relevant
# directories are indicated by environment variables RECOUNT_INPUT,
# RECOUNT_OUTPUT, RECOUNT_REF, RECOUNT_TEMP

set -ex

# Ensure directories
echo "Input dir: ${RECOUNT_INPUT}"
test -n "${RECOUNT_INPUT}"
test -d "${RECOUNT_INPUT}"

echo "Output dir: ${RECOUNT_OUTPUT}"
test -n "${RECOUNT_OUTPUT}"
test -d "${RECOUNT_OUTPUT}"

echo "Ref dir: ${RECOUNT_REF}"
test -n "${RECOUNT_REF}"
test -d "${RECOUNT_REF}"

echo "Temp dir: ${RECOUNT_TEMP}"
test -n "${RECOUNT_TEMP}"
test -d "${RECOUNT_TEMP}"

echo "Big Temp dir: ${RECOUNT_TEMP_BIG}"
test -n "${RECOUNT_TEMP_BIG}"
test -d "${RECOUNT_TEMP_BIG}"

echo "CPUs: ${RECOUNT_CPUS}"
test -n "${RECOUNT_CPUS}"

# Gather inputs
echo "Inputs: $(ls ${RECOUNT_INPUT})"
echo "Refs: $(ls ${RECOUNT_REF})"
echo "Temp: $(ls ${RECOUNT_TEMP})"

INPUT_FILES=`ls ${RECOUNT_INPUT}/*`
test -n "${INPUT_FILES}"

# Run nextflow workflow
if [[ -f /workflow.nf ]] ; then
    mkdir -p ${RECOUNT_TEMP}/nextflow-home ${RECOUNT_TEMP}/nextflow-temp
    chmod -R a+rwx ${RECOUNT_TEMP}/nextflow-home ${RECOUNT_TEMP}/nextflow-temp
    echo "executor.\$local.cpus = ${RECOUNT_CPUS}" > ${RECOUNT_TEMP}/.nx.cfg
    export NXF_TEMP=${RECOUNT_TEMP}/nextflow-temp && \
        nextflow run /workflow.nf \
            -c ${RECOUNT_TEMP}/.nx.cfg \
            -w ${RECOUNT_TEMP}/nextflow-work \
            --in "${INPUT_FILES}" \
            --out "${RECOUNT_OUTPUT}" \
            --ref "${RECOUNT_REF}" \
            --temp "${RECOUNT_TEMP}" \
            --cpus "${RECOUNT_CPUS}" \
            $*
elif [[ -f /Snakefile ]] ; then
    mkdir -p ${RECOUNT_TEMP_BIG}/snakemake-wd
    pushd ${RECOUNT_TEMP_BIG}/snakemake-wd
    CONFIGFILE=""
    if [[ -f "${RECOUNT_TEMP_BIG}/config.json" ]] ; then
        CONFIGFILE="--configfile ${RECOUNT_TEMP_BIG}/config.json"
    fi
    snakemake \
        --snakefile /Snakefile \
        ${CONFIGFILE} \
        --stats "${RECOUNT_OUTPUT}/stats.json" \
        -j "${RECOUNT_CPUS}" \
        $* \
        --config \
            input="${INPUT_FILES}" \
            output="${RECOUNT_OUTPUT}" \
            ref="${RECOUNT_REF}" \
            temp="${RECOUNT_TEMP}" \
            temp_big="${RECOUNT_TEMP_BIG}" \
            keep_bam=1 \
            2>&1 | tee ${RECOUNT_OUTPUT}/std.out
    popd
else
    echo "Could not detect workflow script"
    exit 1
fi

echo SUCCESS
