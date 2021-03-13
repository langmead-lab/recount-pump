#!/bin/bash -l
#SBATCH --partition=skx-normal
#SBATCH --job-name=short-skx-pump
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=1
#SBATCH --time=12:00:00
#SBATCH -A TG-DEB180021
#SBATCH --exclude=c502-043,c502-001,c478-043,c478-031

#runner for recount-pump (Monorail) on TACC/Stampede2
#requires GNU parallel to run pump intra-node processes

module load gnuparallel
module load tacc-singularity

dir=./
export IMAGE=/work/04620/cwilks/singularity_cache/recount-rs5-1.0.6.simg
export REF=hg38
export REFS_DIR=/work/04620/cwilks/monorail-external/refs
export NUM_PUMP_PROCESSES=16
export NUM_CORES=8

#study name/accession, e.g. ERP001942
study=$1
#file with list of runs accessions to process from study
runs_file=$2
#e.g. /scratch/04620/cwilks/workshop
export WORKING_DIR=$3

for f in input output temp temp_big; do mkdir -p $WORKING_DIR/$f ; done

#store the log for each job run
mkdir -p $WORKING_DIR/jobs_run/${SLURM_JOB_ID}

echo -n "" > $WORKING_DIR/${SLURM_JOB_ID}.jobs
for r in `cat $runs_file`; do
    echo "LD_PRELOAD=/work/00410/huang/share/patch/myopen.so /bin/bash -x $dir/run_recount_pump.sh $IMAGE $r $study $REF $NUM_CORES $REFS_DIR > $WORKING_DIR/jobs_run/${SLURM_JOB_ID}/${r}.${study}.pump.run 2>&1" >> $WORKING_DIR/${SLURM_JOB_ID}.jobs
done

parallel -j $NUM_PUMP_PROCESSES < $WORKING_DIR/${SLURM_JOB_ID}.jobs
