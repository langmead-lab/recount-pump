#!/usr/bin/env bash
# $1: number of cores
# $2: output directory -- SPECIFY FULL PATH
# $3: where to find sample fastqs from generate_bioreps.py
# $4: sample name; this is the prefix of "_sim.fastq"
# $5: scratch directory; files are written here first, and relevant output is copied back to $2
# Ex: taskset -c 0,1,2,3 sh run_single_sample_hisat2_sim.sh 4 ./myoutput NA11829_male_CEU_UU_6-1-1 /tmp
# See generate_bioreps.py for how sample data was generated.

TOOL=hisat2

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
# Used version ??? of HISAT2
HISAT2=/software/apps/hisat2/2.1.0/bin/hisat2
# Use HISAT2's tool for extracting splice sites for its junction database
HISAT2SPLICE=/scratch/users/blangme2@jhu.edu/git/hisat2/extract_splice_sites.py
# Specify Python executable/loc of get_junctions.py; PyPy 2.5.0 was used
PYTHON=/scratch/groups/blangme2/software/pypy-6.0.0-linux_x86_64-portable/bin/pypy
SAMTOOLS=/software/apps/samtools/1.9/intel/18.0/bin/samtools

# Specify log filename for recording times
TIMELOG=${MAINOUTPUT}/${TOOL}_${SAMPLE}_times.log
echo > $TIMELOG

## Specify locations of reference-related files
## See create_indexes.sh for index creation script
# HISAT2 index
#HISAT2IDX=/dcl01/leek/data/railsims/indexes_for_paper/hisat2genome
HISAT2IDX=/scratch/groups/blangme2/rail_sims/indexes/genome
#HISAT2IDX=/scratch/groups/blangme2/rail_sims/indexes/hg38_snp

# Generic name of file measuring performance of a given alignment strategy
# Performance is computed with spliced_read_recovery_performance.py; refer to that file for details
PERFORMANCE=perform

## Specify location of annotation
# This is Gencode v12, which may be obtained at ftp://ftp.sanger.ac.uk/pub/gencode/release_12/gencode.v12.annotation.gtf.gz
ANNOTATION=/scratch/groups/blangme2/rail_sims/gencode.v12.annotation.gtf

mkdir -p "${SCRATCH}/${TOOL}/${SAMPLE}"
cd "${SCRATCH}/${TOOL}/${SAMPLE}"

## HISAT2 also uses a list of introns, but here we use a tool that came with HISAT2 to grab splice sites because coordinate system could be different
# Build HISAT2 junction index from GTF
HISAT2ANNOTATION=${SCRATCH}/${TOOL}/${SAMPLE}/junctions_for_hisat.txt

# Flux outputs paired-end reads in one file; split files here
echo 'Building annotation for HISAT2 from GTF...'
$PYTHON $HISAT2SPLICE $ANNOTATION >$HISAT2ANNOTATION
[ ! -f $HISAT2ANNOTATION ] && echo "Did not create junctions_for_hisat.txt" && exit 1

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
echo 'Running HISAT2 on sample '${SAMPLE}' with no annotation and in paired-end mode...'
echo '#'${SAMPLE}' HISAT2 1-pass noann paired' >>$TIMELOG
mkdir -p $OUTPUT/hisat2/noann_paired_1pass
cd $OUTPUT/hisat2/noann_paired_1pass
time ($HISAT2 -x $HISAT2IDX -1 ${LEFT} -2 ${RIGHT} -p $CORES -S Aligned.out.sam --novel-splicesite-outfile novel_splice_sites.txt 2>&1) 2>>$TIMELOG
echo 'Computing precision and recall...'
(cat Aligned.out.sam | $PYTHON $RAILHOME/eval/spliced_read_recovery_performance.py -g -t ${BED} >$PERFORMANCE 2>${PERFORMANCE}_summary)
(cat Aligned.out.sam | $PYTHON $RAILHOME/eval/intron_recovery_performance.py -t ${BED} >${PERFORMANCE}_intron_recovery_summary)
(cat Aligned.out.sam | $PYTHON $RAILHOME/eval/mapping_accuracy.py -t ${BED} -g >${PERFORMANCE}_mapping_accuracy_summary)
(cat Aligned.out.sam | $PYTHON $RAILHOME/eval/mapping_accuracy.py -t ${BED} -c 0.1 -g >${PERFORMANCE}_mapping_accuracy_SC_summary)
echo 'Running HISAT2 on sample '${SAMPLE}' with annotation and in paired-end mode...'
echo '#'${SAMPLE}' HISAT2 1-pass ann paired' >>$TIMELOG
mkdir -p $OUTPUT/hisat2/ann_paired_1pass
cd $OUTPUT/hisat2/ann_paired_1pass
time ($HISAT2 -x $HISAT2IDX -1 ${LEFT} -2 ${RIGHT} -p $CORES -S Aligned.out.sam --novel-splicesite-outfile novel_splice_sites.txt --novel-splicesite-infile $HISAT2ANNOTATION 2>&1) 2>>$TIMELOG
echo 'Computing precision and recall...'
(cat Aligned.out.sam | $PYTHON $RAILHOME/eval/spliced_read_recovery_performance.py -g -t ${BED} >$PERFORMANCE 2>${PERFORMANCE}_summary)
(cat Aligned.out.sam | $PYTHON $RAILHOME/eval/intron_recovery_performance.py -t ${BED} >${PERFORMANCE}_intron_recovery_summary)
(cat Aligned.out.sam | $PYTHON $RAILHOME/eval/mapping_accuracy.py -t ${BED} -g >${PERFORMANCE}_mapping_accuracy_summary)
(cat Aligned.out.sam | $PYTHON $RAILHOME/eval/mapping_accuracy.py -t ${BED} -c 0.1 -g >${PERFORMANCE}_mapping_accuracy_SC_summary)
echo 'Running second pass of HISAT2 on sample '${SAMPLE}' with no annotation and in paired-end mode...'
echo '#'${SAMPLE}' HISAT2 2-pass noann paired' >>$TIMELOG
mkdir -p $OUTPUT/hisat2/noann_paired_2pass
cd $OUTPUT/hisat2/noann_paired_2pass
time ($HISAT2 -x $HISAT2IDX -1 ${LEFT} -2 ${RIGHT} -p $CORES -S Aligned.out.sam --novel-splicesite-infile $OUTPUT/hisat2/noann_paired_1pass/novel_splice_sites.txt 2>&1) 2>>$TIMELOG
echo 'Computing precision and recall...'
(cat Aligned.out.sam | $PYTHON $RAILHOME/eval/spliced_read_recovery_performance.py -g -t ${BED} >$PERFORMANCE 2>${PERFORMANCE}_summary)
(cat Aligned.out.sam | $PYTHON $RAILHOME/eval/intron_recovery_performance.py -t ${BED} >${PERFORMANCE}_intron_recovery_summary)
(cat Aligned.out.sam | $PYTHON $RAILHOME/eval/mapping_accuracy.py -t ${BED} -g >${PERFORMANCE}_mapping_accuracy_summary)
(cat Aligned.out.sam | $PYTHON $RAILHOME/eval/mapping_accuracy.py -t ${BED} -c 0.1 -g >${PERFORMANCE}_mapping_accuracy_SC_summary)
echo 'Running second pass of HISAT2 on sample '${SAMPLE}' with annotation and in paired-end mode...'
echo '#'${SAMPLE}' HISAT2 2-pass ann paired' >>$TIMELOG
mkdir -p $OUTPUT/hisat2/ann_paired_2pass
cd $OUTPUT/hisat2/ann_paired_2pass
time ($HISAT2 -x $HISAT2IDX -1 ${LEFT} -2 ${RIGHT} -p $CORES -S Aligned.out.sam --novel-splicesite-infile $OUTPUT/hisat2/ann_paired_1pass/novel_splice_sites.txt 2>&1) 2>>$TIMELOG
echo 'Computing precision and recall...'
(cat Aligned.out.sam | $PYTHON $RAILHOME/eval/spliced_read_recovery_performance.py -g -t ${BED} >$PERFORMANCE 2>${PERFORMANCE}_summary)
(cat Aligned.out.sam | $PYTHON $RAILHOME/eval/intron_recovery_performance.py -t ${BED} >${PERFORMANCE}_intron_recovery_summary)
(cat Aligned.out.sam | $PYTHON $RAILHOME/eval/mapping_accuracy.py -t ${BED} -g >${PERFORMANCE}_mapping_accuracy_summary)
(cat Aligned.out.sam | $PYTHON $RAILHOME/eval/mapping_accuracy.py -t ${BED} -c 0.1 -g >${PERFORMANCE}_mapping_accuracy_SC_summary)

echo 'Delete decompressed FASTQs...'
rm -f ${LEFT} ${RIGHT} ${BED}

echo 'Move results to final destination...'
rm -rf ${SAMPLEOUTPUT}/hisat2
cp -r ${OUTPUT}/hisat2 $SAMPLEOUTPUT
rm -rf ${OUTPUT}/hisat2
