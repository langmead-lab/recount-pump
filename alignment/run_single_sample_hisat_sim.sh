#!/usr/bin/env bash
# $1: number of cores
# $2: output directory -- SPECIFY FULL PATH
# $3: where to find sample fastqs from generate_bioreps.py
# $4: sample name; this is the prefix of "_sim.fastq"
# $5: scratch directory; files are written here first, and relevant output is copied back to $2
# Ex: taskset -c 0,1,2,3 sh run_single_sample_hisat_sim.sh 4 ./myoutput NA11829_male_CEU_UU_6-1-1 /tmp
# See generate_bioreps.py for how sample data was generated.

d=$(dirname $0)
TOOL=hisat

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
RAILHOME=/scratch/users/blangme2@jhu.edu/git/rail

## Specify locations of executables
# Used version 0.1.6-beta of HISAT
HISAT_HOME=/home-1/blangme2@jhu.edu/software/hisat-0.1.6-beta
HISAT=${HISAT_HOME}/${TOOL}
# Use HISAT's tool for extracting splice sites for its junction database
HISATSPLICE=${HISAT_HOME}/extract_splice_sites.py
# Specify Python executable/loc of get_junctions.py; PyPy 2.5.0 was used
PYTHON=/scratch/groups/blangme2/software/pypy-6.0.0-linux_x86_64-portable/bin/pypy
SAMTOOLS=/software/apps/samtools/1.9/intel/18.0/bin/samtools

# Specify log filename for recording times
TIMELOG=${MAINOUTPUT}/${TOOL}_${SAMPLE}_times.log
echo > $TIMELOG

## Specify locations of reference-related files
## See create_indexes.sh for index creation script
# HISAT index
HISATIDX=/scratch/groups/blangme2/rail_sims/indexes/genome

# Generic name of file measuring performance of a given alignment strategy
# Performance is computed with spliced_read_recovery_performance.py; refer to that file for details
PERFORMANCE=perform

## Specify location of annotation
# This is Gencode v12, which may be obtained at ftp://ftp.sanger.ac.uk/pub/gencode/release_12/gencode.v12.annotation.gtf.gz
ANNOTATION=/scratch/groups/blangme2/rail_sims/gencode.v12.annotation.gtf

mkdir -p "${SCRATCH}/${TOOL}/${SAMPLE}"
cd "${SCRATCH}/${TOOL}/${SAMPLE}"

## HISAT also uses a list of introns, but here we use a tool that came with HISAT to grab splice sites because coordinate system could be different
# Build HISAT junction index from GTF
HISATANNOTATION=${SCRATCH}/${TOOL}/${SAMPLE}/junctions_for_hisat.txt

# Flux outputs paired-end reads in one file; split files here
echo 'Building annotation for HISAT from GTF...'
$PYTHON $HISATSPLICE $ANNOTATION >$HISATANNOTATION
[ ! -f $HISATANNOTATION ] && echo "Did not create junctions_for_hisat.txt" && exit 1

echo 'Decompressing FASTQs...'
LEFT=${SCRATCH}/${TOOL}/${SAMPLE}_sim_left.fastq
RIGHT=${SCRATCH}/${TOOL}/${SAMPLE}_sim_right.fastq
BED=${SCRATCH}/${TOOL}/${SAMPLE}_sim.bed
zstd -dc $DATADIR/${SAMPLE}_sim_left.fastq.zst  -o ${LEFT}
zstd -dc $DATADIR/${SAMPLE}_sim_right.fastq.zst -o ${RIGHT}
zstd -dc $DATADIR/${SAMPLE}_sim.bed.zst         -o ${BED}

cd $MAINOUTPUT
mkdir -p ${SAMPLE}
SAMPLEOUTPUT=${MAINOUTPUT}/${SAMPLE}

# Run simulations
OUTPUT=$SCRATCH/${TOOL}/${SAMPLE}
echo 'Running HISAT on sample '${SAMPLE}' with no annotation and in paired-end mode...'
echo '#'${SAMPLE}' HISAT 1-pass noann paired' >>$TIMELOG
mkdir -p $OUTPUT/hisat/noann_paired_1pass
cd $OUTPUT/hisat/noann_paired_1pass
time ($HISAT -x $HISATIDX -1 ${LEFT} -2 ${RIGHT} -p $CORES -S Aligned.out.sam --novel-splicesite-outfile novel_splice_sites.txt 2>&1) 2>>$TIMELOG
echo 'Computing precision and recall...'
(cat Aligned.out.sam | $PYTHON $d/eval/spliced_read_recovery_performance.py -g -t ${BED} >$PERFORMANCE 2>${PERFORMANCE}_summary)
(cat Aligned.out.sam | $PYTHON $d/eval/intron_recovery_performance.py -t ${BED} >${PERFORMANCE}_intron_recovery_summary)
(cat Aligned.out.sam | $PYTHON $d/eval/mapping_accuracy.py -t ${BED} -g >${PERFORMANCE}_mapping_accuracy_summary)
(cat Aligned.out.sam | $PYTHON $d/eval/mapping_accuracy.py -t ${BED} -c 0.1 -g >${PERFORMANCE}_mapping_accuracy_SC_summary)
echo 'Running HISAT on sample '${SAMPLE}' with annotation and in paired-end mode...'
echo '#'${SAMPLE}' HISAT 1-pass ann paired' >>$TIMELOG
mkdir -p $OUTPUT/hisat/ann_paired_1pass
cd $OUTPUT/hisat/ann_paired_1pass
time ($HISAT -x $HISATIDX -1 ${LEFT} -2 ${RIGHT} -p $CORES -S Aligned.out.sam --novel-splicesite-outfile novel_splice_sites.txt --novel-splicesite-infile $HISATANNOTATION 2>&1) 2>>$TIMELOG
echo 'Computing precision and recall...'
(cat Aligned.out.sam | $PYTHON $d/eval/spliced_read_recovery_performance.py -g -t ${BED} >$PERFORMANCE 2>${PERFORMANCE}_summary)
(cat Aligned.out.sam | $PYTHON $d/eval/intron_recovery_performance.py -t ${BED} >${PERFORMANCE}_intron_recovery_summary)
(cat Aligned.out.sam | $PYTHON $d/eval/mapping_accuracy.py -t ${BED} -g >${PERFORMANCE}_mapping_accuracy_summary)
(cat Aligned.out.sam | $PYTHON $d/eval/mapping_accuracy.py -t ${BED} -c 0.1 -g >${PERFORMANCE}_mapping_accuracy_SC_summary)
echo 'Running second pass of HISAT on sample '${SAMPLE}' with no annotation and in paired-end mode...'
echo '#'${SAMPLE}' HISAT 2-pass noann paired' >>$TIMELOG
mkdir -p $OUTPUT/hisat/noann_paired_2pass
cd $OUTPUT/hisat/noann_paired_2pass
time ($HISAT -x $HISATIDX -1 ${LEFT} -2 ${RIGHT} -p $CORES -S Aligned.out.sam --novel-splicesite-infile $OUTPUT/hisat/noann_paired_1pass/novel_splice_sites.txt 2>&1) 2>>$TIMELOG
echo 'Computing precision and recall...'
(cat Aligned.out.sam | $PYTHON $d/eval/spliced_read_recovery_performance.py -g -t ${BED} >$PERFORMANCE 2>${PERFORMANCE}_summary)
(cat Aligned.out.sam | $PYTHON $d/eval/intron_recovery_performance.py -t ${BED} >${PERFORMANCE}_intron_recovery_summary)
(cat Aligned.out.sam | $PYTHON $d/eval/mapping_accuracy.py -t ${BED} -g >${PERFORMANCE}_mapping_accuracy_summary)
(cat Aligned.out.sam | $PYTHON $d/eval/mapping_accuracy.py -t ${BED} -c 0.1 -g >${PERFORMANCE}_mapping_accuracy_SC_summary)
echo 'Running second pass of HISAT on sample '${SAMPLE}' with annotation and in paired-end mode...'
echo '#'${SAMPLE}' HISAT 2-pass ann paired' >>$TIMELOG
mkdir -p $OUTPUT/hisat/ann_paired_2pass
cd $OUTPUT/hisat/ann_paired_2pass
time ($HISAT -x $HISATIDX -1 ${LEFT} -2 ${RIGHT} -p $CORES -S Aligned.out.sam --novel-splicesite-infile $OUTPUT/hisat/ann_paired_1pass/novel_splice_sites.txt 2>&1) 2>>$TIMELOG
echo 'Computing precision and recall...'
(cat Aligned.out.sam | $PYTHON $d/eval/spliced_read_recovery_performance.py -g -t ${BED} >$PERFORMANCE 2>${PERFORMANCE}_summary)
(cat Aligned.out.sam | $PYTHON $d/eval/intron_recovery_performance.py -t ${BED} >${PERFORMANCE}_intron_recovery_summary)
(cat Aligned.out.sam | $PYTHON $d/eval/mapping_accuracy.py -t ${BED} -g >${PERFORMANCE}_mapping_accuracy_summary)
(cat Aligned.out.sam | $PYTHON $d/eval/mapping_accuracy.py -t ${BED} -c 0.1 -g >${PERFORMANCE}_mapping_accuracy_SC_summary)

echo 'Delete decompressed FASTQs...'
rm -f ${LEFT} ${RIGHT} ${BED}

echo 'Move results to final destination...'
rm -rf ${SAMPLEOUTPUT}/hisat
cp -r ${OUTPUT}/hisat $SAMPLEOUTPUT
rm -rf ${OUTPUT}/hisat
