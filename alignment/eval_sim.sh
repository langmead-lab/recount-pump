#!/usr/bin/env bash
# $1: experimental setup
# $2: name of input sample
#
# See generate_bioreps.py for how sample data was generated.

# Current samples:
# HG00111_female_GBR_CNAG_CRG_2-1-1
# HG00152_male_GBR_LUMC_7-1-1

# Current setups:
# humansim_annotation_500oh
# humansim_annotation_50oh
# humansim_annotation
# humansim_hg38
# humansim_recount2_500oh
# humansim_recount2_50oh
# humansim_recount2

if [[ -z "${1}" ]] ; then
    echo "Specify sample (e.g. HG00111_female_GBR_CNAG_CRG_2-1-1) as 1st argument"
    exit 1
fi
if [[ -z "${2}" ]] ; then
    echo "Specify experiment type (e.g. humansim_recount2_50oh) as 2nd argument"
    exit 1
fi

set -ex

mkdir -p output

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

# Specify data directory; fastqs should be of the form [SAMPLE NAME]_sim.fastq; Flux beds should be
# of form [SAMPLE_NAME]_sim.bed
data=/home-1/cwilks3@jhu.edu/storage/cwilks/recount-pump/destination/humansim_local
test -d "${data}"
test -d "${data}/${2}.output"

samp_no_dash=$(echo ${1} | sed 's/-/_/g')
bam=$(ls -1 ${data}/${2}.output/${samp_no_dash}*.bam)
test -f ${bam}

PYTHON=/scratch/groups/blangme2/software/pypy-6.0.0-linux_x86_64-portable/bin/pypy
SAMTOOLS=/software/apps/samtools/1.9/intel/18.0/bin/samtools
which $PYTHON
which $SAMTOOLS

echo "Overlap-level (1/4)..."
samtools view ${bam} | \
    $PYTHON eval/spliced_read_recovery_performance.py -g -t ${bed} >perf 2>perf_summary

echo "Intron-level (2/4)..."
samtools view ${bam} | \
    $PYTHON eval/intron_recovery_performance.py -t ${bed} >perf_intron_recovery_summary

echo "Alignment and base-level, no soft clipping (3/4)..."
samtools view ${bam} | \
    $PYTHON eval/mapping_accuracy.py -t ${bed} -g >perf_mapping_accuracy_summary

echo "Alignment and base-level, with soft clipping (4/4)..."
samtools view ${bam} | \
    $PYTHON eval/mapping_accuracy.py -t ${bed} -c 0.1 -g >perf_mapping_accuracy_SC_summary
