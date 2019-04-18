#!/usr/bin/env bash
# $1: experimental setup
# $2: name of input sample
#
# See generate_bioreps.py for how sample data was generated.

# Current samples:
# HG00111_female_GBR_CNAG_CRG_2-1-1
# HG00152_male_GBR_LUMC_7-1-1

# Current setups:
# hg19_annotation_500
# hg19_annotation_100
# hg19_annotation_50
# hg19
# hg19_snaptron_500
# hg19_snaptron_100
# hg19_snaptron_50

if [[ -z "${1}" ]] ; then
    echo "Specify sample (e.g. HG00111_female_GBR_CNAG_CRG_2-1-1) as 1st argument"
    exit 1
fi

set -ex

mkdir -p sim_data
url_base=s3://recount-reads/human_sim
if [[ ! -d sim_data/${1} ]] ; then
    echo "Downloading bed file from simulation"
    url="${url_base}/${1}_sim.bed.zst"
    echo "Should be at ${url}"
    aws --profile jhu-langmead s3 cp ${url} sim_data/${1}/sim.bed.zst
    zstd -d sim_data/${1}/sim.bed.zst
fi

bed=sim_data/${1}/sim.bed
test -f ${bed}

