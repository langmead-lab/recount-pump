#!/bin/bash -l
#SBATCH --partition=flat-quadrant
#SBATCH --job-name=knl-unify
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=1
#SBATCH --time=24:00:00
#SBATCH -A TG-DEB180021
#SBATCH --exclude=c502-043,c502-001,c478-043,c478-031
#runner for recount-unify (post-pump Monorail) on TACC/Stampede2
set -exo pipefail

#requires GNU parallel to run pump intra-node processes

module load gnuparallel
module load tacc-singularity

dir=./
export IMAGE=/work/04620/cwilks/singularity_cache/recount-unify-1.0.4.simg
export REF=hg38
export REFS_DIR=/work/04620/cwilks/monorail-external/refs
export NUM_CORES=80

#default project name (sra, tcga, gtex, etc...) and compilation ID (for rail_id generation)
export PROJECT_SHORT_NAME_AND_ID='sra:101'

#e.g. /scratch/04620/cwilks/workshop
WORKING_DIR=$1
STUDY=$2
PUMP_OUTPUT_DIR=$3

JOB_ID=$SLURM_JOB_ID
export WORKING_DIR=$WORKING_DIR/unify/${STUDY}.${JOB_ID}
mkdir -p $WORKING_DIR
pump_study_samples_file=$WORKING_DIR/input_samples.tsv
echo "study	sample" > $pump_study_samples_file
find $PUMP_OUTPUT_DIR -name "*.manifest" | sed 's#^.\+att0/\([^!]\+\)!\([^!]\+\)!.\+$#\2\t\1#' >> $pump_study_samples_file

num_samples=$(tail -n+2 $pump_study_samples_file | wc -l)
echo "number of samples in $STUDY's pump output for $PUMP_OUTPUT_DIR: $num_samples"

/bin/bash $dir/run_recount_unify.sh $IMAGE $REF $REFS_DIR $WORKING_DIR $PUMP_OUTPUT_DIR $pump_study_samples_file $NUM_CORES $PROJECT_SHORT_NAME_AND_ID > $WORKING_DIR/unify.run 2>&1
