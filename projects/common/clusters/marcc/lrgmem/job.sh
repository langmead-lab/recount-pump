#!/bin/bash -l
#SBATCH --partition=lrgmem
#SBATCH --job-name=rclrg4
#SBATCH --nodes=1
#SBATCH --mem=900G
#SBATCH --time=72:00:00
#SBATCH --ntasks-per-node=48
#SBATCH --exclude=bigmem0041,bigmem0032,bigmem0037,bigmem0029,bigmem0030,bigmem0040

#e.g. gtexv8, gtex, tcga
tranche=gtexv8

export SINGULARITY_CACHEDIR=/net/langmead-bigmem-ib.bluecrab.cluster/storage/cwilks/recount-pump/recount/singularity_cache
module load singularity
umask 0077
#MARCC sets PERL5LIB to something which won't work
#with HISAT2
export PERL5LIB=

rm -rf /dev/shm/monorail*
mkdir -p /dev/shm/monorail
chmod 700 /dev/shm/monorail

~/storage/cwilks/miniconda2/bin/python /home-1/cwilks3@jhu.edu/storage/cwilks/recount-pump/src/cluster.py run --ini-base creds --cluster-ini creds/cluster4_shm.ini $tranche
