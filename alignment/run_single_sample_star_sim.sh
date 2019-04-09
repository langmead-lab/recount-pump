#!/usr/bin/env bash
# $1: number of cores
# $2: output directory -- SPECIFY FULL PATH
# $3: where to find sample fastqs from generate_bioreps.py
# $4: sample name; this is the prefix of "_sim.fastq"
# $5: scratch directory; files are written here first, and relevant output is copied back to $2
# Ex: taskset -c 0,1,2,3 sh run_single_sample_star_sim.sh 4 ./myoutput NA11829_male_CEU_UU_6-1-1 /tmp
# See generate_bioreps.py for how sample data was generated.

d=$(dirname $0)
TOOL=star

# Specify number of parallel processes for each program
CORES=8

# Specify FULL PATH to output directory
MAINOUTPUT=/scratch/groups/blangme2/rail_sims/output
mkdir -p ${MAINOUTPUT}

# Specify data directory; fastqs should be of the form [SAMPLE NAME]_sim.fastq; Flux beds should be
# of form [SAMPLE_NAME]_sim.bed
DATADIR=/scratch/groups/blangme2/rail_sims/data

# Specify sample name at command line
SAMPLE=$1

# Temp dir
SCRATCH=/scratch/groups/blangme2/rail_sims/SCRATCH
mkdir -p ${SCRATCH}

## Specify locations of executables
# Used version STAR_2.6.1a_08-27 of STAR
STAR=/scratch/groups/blangme2/software/miniconda3/bin/STAR
# Specify Python executable/loc of get_junctions.py; PyPy 2.5.0 was used
PYTHON=/scratch/groups/blangme2/software/pypy-6.0.0-linux_x86_64-portable/bin/pypy
SAMTOOLS=/software/apps/samtools/1.9/intel/18.0/bin/samtools

# Specify log filename for recording times
TIMELOG=${MAINOUTPUT}/${TOOL}_${SAMPLE}_times.log
echo > ${TIMELOG}

## Specify locations of reference-related files
## See create_indexes.sh for index creation script
# STAR index
STARIDX=/scratch/groups/blangme2/rail_sims/indexes/star
STARANNIDX=/scratch/groups/blangme2/rail_sims/indexes/star_ann
# Overhang length for STAR; this should ideally be max read length - 1
OVERHANG=75

# Generic name of file measuring performance of a given alignment strategy
# Performance is computed with spliced_read_recovery_performance.py; refer to that file for details
PERFORMANCE=perform

mkdir -p "${SCRATCH}/${TOOL}/${SAMPLE}"
cd "${SCRATCH}/${TOOL}/${SAMPLE}"

## STAR requires its own annotation format that lists introns directly; conversion is done by get_junctions.py
# Build STAR junction index from GTF
STARANNOTATION=${SCRATCH}/${TOOL}/${SAMPLE}/junctions_for_star.txt

echo 'Decompressing FASTQs...'
LEFT=${SCRATCH}/${TOOL}/${SAMPLE}_sim_left.fastq
RIGHT=${SCRATCH}/${TOOL}/${SAMPLE}_sim_right.fastq
BED=${SCRATCH}/${TOOL}/${SAMPLE}_sim.bed
zstd -dc $DATADIR/${SAMPLE}_sim_left.fastq.zst  -o ${LEFT}
zstd -dc $DATADIR/${SAMPLE}_sim_right.fastq.zst -o ${RIGHT}
zstd -dc $DATADIR/${SAMPLE}_sim.bed.zst         -o ${BED}

## Where Feb 2009 hg19 chromosome files are located; download them at http://hgdownload.cse.ucsc.edu/goldenPath/hg19/bigZips/chromFa.tar.gz
# These are here because it's necessary to build a new STAR index for its 2-pass and annotation protocols
FADIR=/scratch/groups/blangme2/rail_sims/indexes

# Create STAR index including annotation
echo 'Creating new STAR index including splice junctions...'
echo '#STAR index pre-1-pass ann' >>$TIMELOG

cd $MAINOUTPUT
mkdir -p ${SAMPLE}
SAMPLEOUTPUT=${MAINOUTPUT}/${SAMPLE}

# Run simulations
OUTPUT=$SCRATCH/${TOOL}/${SAMPLE}
# STAR protocol for 2-pass execution w/ index construction is described on pp. 43-44 of the supplement of the RGASP spliced alignment paper
# (http://www.nature.com/nmeth/journal/v10/n12/extref/nmeth.2722-S1.pdf)
echo 'Running STAR on sample '${SAMPLE}' with no regenerated genome/no annotation and in paired-end mode...'
echo '#'${SAMPLE}' STAR 2-pass nogen noann paired' >>$TIMELOG
mkdir -p ${OUTPUT}/${TOOL}/nogen_noann_paired_2pass
cd ${OUTPUT}/${TOOL}/nogen_noann_paired_2pass
time ($STAR --genomeDir $STARIDX --readFilesIn ${LEFT} ${RIGHT} --runThreadN $CORES --twopass1readsN -1 --sjdbOverhang $OVERHANG --twopassMode Basic >&1) 2>>$TIMELOG
echo 'Computing precision and recall...'
(cat Aligned.out.sam | $PYTHON ${d}/eval/spliced_read_recovery_performance.py -g -t ${BED} >$PERFORMANCE 2>${PERFORMANCE}_summary)
(cat Aligned.out.sam | $PYTHON ${d}/eval/intron_recovery_performance.py -t ${BED} >${PERFORMANCE}_intron_recovery_summary)
(cat Aligned.out.sam | $PYTHON ${d}/eval/mapping_accuracy.py -t ${BED} -g >${PERFORMANCE}_mapping_accuracy_summary)
(cat Aligned.out.sam | $PYTHON ${d}/eval/mapping_accuracy.py -t ${BED} -c 0.1 -g >${PERFORMANCE}_mapping_accuracy_SC_summary)

echo 'Running STAR on sample '${SAMPLE}' with no annotation and in paired-end mode...'
echo '#'${SAMPLE}' STAR 1-pass noann paired' >>$TIMELOG
mkdir -p ${OUTPUT}/${TOOL}/noann_paired_1pass
cd ${OUTPUT}/${TOOL}/noann_paired_1pass
time ($STAR --genomeDir $STARIDX --readFilesIn ${LEFT} ${RIGHT} --runThreadN $CORES 2>&1) 2>>$TIMELOG
echo 'Computing precision and recall...'
(cat Aligned.out.sam | $PYTHON ${d}/eval/spliced_read_recovery_performance.py -g -t ${BED} >$PERFORMANCE 2>${PERFORMANCE}_summary)
(cat Aligned.out.sam | $PYTHON ${d}/eval/intron_recovery_performance.py -t ${BED} >${PERFORMANCE}_intron_recovery_summary)
(cat Aligned.out.sam | $PYTHON ${d}/eval/mapping_accuracy.py -t ${BED} -g >${PERFORMANCE}_mapping_accuracy_summary)
(cat Aligned.out.sam | $PYTHON ${d}/eval/mapping_accuracy.py -t ${BED} -c 0.1 -g >${PERFORMANCE}_mapping_accuracy_SC_summary)

echo 'Running STAR on sample '${SAMPLE}' with annotation and in paired-end mode...'
echo '#'${SAMPLE}' STAR 1-pass ann paired' >>$TIMELOG
mkdir -p ${OUTPUT}/${TOOL}/ann_paired_1pass
cd ${OUTPUT}/${TOOL}/ann_paired_1pass
time ($STAR --genomeDir $STARANNIDX --readFilesIn ${LEFT} ${RIGHT} --runThreadN $CORES 2>&1) 2>>$TIMELOG
echo 'Computing precision and recall...'
(cat Aligned.out.sam | $PYTHON ${d}/eval/spliced_read_recovery_performance.py -g -t ${BED} >$PERFORMANCE 2>${PERFORMANCE}_summary)
(cat Aligned.out.sam | $PYTHON ${d}/eval/intron_recovery_performance.py -t ${BED} >${PERFORMANCE}_intron_recovery_summary)
(cat Aligned.out.sam | $PYTHON ${d}/eval/mapping_accuracy.py -t ${BED} -g >${PERFORMANCE}_mapping_accuracy_summary)
(cat Aligned.out.sam | $PYTHON ${d}/eval/mapping_accuracy.py -t ${BED} -c 0.1 -g >${PERFORMANCE}_mapping_accuracy_SC_summary)

echo 'Delete decompressed FASTQs...'
rm -f ${LEFT} ${RIGHT} ${BED}

echo 'Move results to final destination...'
dir="${SAMPLEOUTPUT}/${TOOL}"
if [ -d "${dir}" ] ; then
    echo "WARNING: deleting existing directory \"${dir}\""
    rm -rf ${dir}
fi
mkdir -p ${SAMPLEOUTPUT}/${TOOL}
mv ${OUTPUT}/${TOOL}/* ${SAMPLEOUTPUT}/${TOOL}/
