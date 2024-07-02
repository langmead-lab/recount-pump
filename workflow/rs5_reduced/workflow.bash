#!/usr/bin/env bash

# Author: Ben Langmead
#  Email: langmea@cs.jhu.edu
#   Date: 1/5/2018
# Updates: Chris Wilks
#  Email: broadsword@gmail.com
#  Latest Date: 03/06/2023
#  Latest updates: slimmed down version just doing primary alignment phase (no hisat2/unmapped reads keeping) and no Salmon

# Designed to run the nextflow script from inside a container, where relevant
# directories are indicated by environment variables RECOUNT_INPUT,
# RECOUNT_OUTPUT, RECOUNT_REF, RECOUNT_TEMP

# For dbGaP downloads: you will need to set the NGC environment variable to the 
# container visible path to your study-specific dbGaP key file (e.g. prj_*.ngc)

# For overriding elements of the Snakemake config (e.g. the path to the download script for instance)
# define CONFIGFILE="/path/to/config.json" on a container reachable path
# possible config params:

# download_exe
# bamcount_exe
# temp
# temp_big
# input (input file string)
# output (final output path)
# keep_bam
# keep_fastq
# keep_unmapped_fastq
# ref (path to overall reference location (e.g. parent dir of "hg38")
# bw_bed (default exons.bed)
# unique_qual (default 10)
# featureCounts (extra params for FC, default '')
# fc_unique_qual (default 10)
# star_args (extra params for star, default '')
# star_no_shared (dont use shared mem mode, default '0' i.e. use shared mem)
# fastq_dump_args (extra params for fastq_dump, default '')
# fastq_dump_retries (default 2)
# prefetch_args (default '--max-size 200G -L info')

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

extra_params=""
if [[ ! -z $KEEP_BAM ]]; then
    extra_params='keep_bam=1'
    echo "Keeping the BAM"
fi

if [[ ! -z $KEEP_FASTQ ]]; then
    extra_params=$extra_params' keep_fastq=1'
    echo "Keeping the FASTQs"
fi

if [[ ! -z $KEEP_UNMAPPED_FASTQ ]]; then
    extra_params=$extra_params' keep_unmapped_fastq=1'
    echo "Keeping the unmapped FASTQs"
fi

#some cases STAR will need to be run w/o shared memory
if [[ ! -z $NO_SHARED_MEM ]]; then
    extra_params=$extra_params' star_no_shared=1'
    echo "STAR will run w/o sharing the index"
fi

if [[ -f /Snakefile.extra_bamcount ]] ; then
    mkdir -p ${RECOUNT_TEMP_BIG}/snakemake-wd
    pushd ${RECOUNT_TEMP_BIG}/snakemake-wd
    #CONFIGFILE should be set to container reachable path to a json file
    if [[ -n $CONFIGFILE ]]; then
        CONFIGFILE="--configfile $CONFIGFILE"
    fi
    #if CONFIGFILE not set but a config.json file is in the TEMP_BIG path already, use that
    if [[ -z $CONFIGFILE && -f "${RECOUNT_TEMP_BIG}/config.json" ]] ; then
        CONFIGFILE="--configfile ${RECOUNT_TEMP_BIG}/config.json"
    fi
    #otherwise set to empty string
    if [[ -z $CONFIGFILE ]]; then
        CONFIGFILE=""
    fi
    snakemake \
        --snakefile /Snakefile.extra_bamcount \
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
            $extra_params 2>&1 | tee ${RECOUNT_OUTPUT}/std.out

    done=`fgrep 'steps (100%) done' ${RECOUNT_OUTPUT}/std.out`
    popd
    if [[ -z $done ]]; then
        echo "FAILURE running recount-pump"
        exit 1
    fi
else
    echo "Could not detect workflow script"
    exit 1
fi

echo SUCCESS
