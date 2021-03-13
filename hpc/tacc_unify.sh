#!/usr/bin/env bash
#runner for recount-unify (post-pump Monorail) on TACC/Stampede2
sed -exo pipefail

dir=$(dirname $0)
export IMAGE=/work/04620/cwilks/singularity_cache/recount-unify-1.0.4.simg
export REF=hg38
export REFS_DIR=/work/04620/cwilks/monorail-external/refs
export NUM_CORES=40

#default project name (sra, tcga, gtex, etc...) and compilation ID (for rail_id generation)
export PROJECT_SHORT_NAME_AND_ID='sra:101'

e.g. /scratch/04620/cwilks/workshop
working_dir=$1

mkdir -p $working_dir/unify

pump_study_output_path=$working_dir/output
pump_study_samples_file=$working_dir/samples.tsv
#find $pump_study_output_path  -name "*.manifest" | perl -ne 'BEGIN { print "study\tsample\n"; } chomp; $f=$_; @f=split(/\//,$f); $fname=pop(@f); @f=split(/!/,$fname); $run=shift(@f); $study=shift(@f); print "$study\t$run\n";' > $pump_study_samples_file
echo "study	sample" > $pump_study_samples_file
find $pump_study_output_path  -name "*.manifest" | sed 's/^.+\/([^\/!])+!([^!]+)!.+$/$1\t$2/'

num_samples=$(tail n+2 $pump_study_samples_file | wc -l)
echo "number of samples in pump output for $working_dir/output: $num_samples"

/bin/bash $dir/run_recount_unify.sh $IMAGE $REF $REFS_DIR $working_dir/unify $pump_study_output_path $pump_study_samples_file $NUM_CORES $REFS_DIR > $working_dir/${run}.${study}.unify.run 2>&1
