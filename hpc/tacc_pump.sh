#!/bin/bash -l
#SBATCH --partition=flat-quadrant
#SBATCH --job-name=knl-pump
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=1
#SBATCH --time=12:00:00
#SBATCH -A TG-DEB180021
#SBATCH --exclude=c502-043,c502-001,c478-043,c478-031

#runner for recount-pump (Monorail) on TACC/Stampede2
#requires GNU parallel to run pump intra-node processes

module load gnuparallel
module load tacc-singularity

#e.g. /work/04620/cwilks/monorail-external/singularity
dir=./
export IMAGE=/work/04620/cwilks/singularity_cache/recount-rs5-1.0.6.simg
export REF=hg38
export REFS_DIR=/work/04620/cwilks/monorail-external/refs
export NUM_PUMP_PROCESSES=16
export NUM_CORES=8

#study name/accession, e.g. ERP001942
study=$1
#file with list of runs accessions to process from study
#e.g. /home1/04620/cwilks/scratch/workshop/SRP096788.runs.txt
runs_file=$2
#e.g. /scratch/04620/cwilks/workshop
export WORKING_DIR=$3

JOB_ID=$SLURM_JOB_ID
export WORKING_DIR=$WORKING_DIR/pump/${study}.${JOB_ID}
for f in input output temp temp_big; do mkdir -p $WORKING_DIR/$f ; done

#store the log for each job run
mkdir -p $WORKING_DIR/jobs_run/${JOB_ID}

echo -n "" > $WORKING_DIR/pump.jobs
for r in `cat $runs_file`; do
    echo "LD_PRELOAD=/work/00410/huang/share/patch/myopen.so /bin/bash -x $dir/run_recount_pump.sh $IMAGE $r $study $REF $NUM_CORES $REFS_DIR > $WORKING_DIR/${r}.${study}.pump.run 2>&1" >> $WORKING_DIR/pump.jobs
done

#ignore failures
parallel -j $NUM_PUMP_PROCESSES < $WORKING_DIR/pump.jobs || true
