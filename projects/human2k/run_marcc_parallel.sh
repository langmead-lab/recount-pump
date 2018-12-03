#!/bin/bash -l
#SBATCH
#SBATCH --partition=parallel
#SBATCH --nodes=1
#SBATCH --mem=100G
#SBATCH --time=44:00:00
#SBATCH --ntasks-per-node=24

d=/scratch/users/blangme2@jhu.edu/git/recount-pump

python ${d}/src/cluster.py run \
    --ini-base ${d}/projects/human2k/creds \
    --cluster-ini ~/.recount/cluster-parallel.ini \
    1
