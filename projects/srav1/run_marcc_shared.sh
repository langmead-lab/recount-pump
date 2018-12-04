#!/bin/bash -l
#SBATCH
#SBATCH --partition=shared
#SBATCH --nodes=1
#SBATCH --mem=40G
#SBATCH --time=44:00:00
#SBATCH --ntasks-per-node=8

d=/scratch/users/blangme2@jhu.edu/git/recount-pump

python ${d}/src/cluster.py run \
    --ini-base ${d}/projects/srav1/creds \
    --cluster-ini ~/.recount/cluster-shared.ini \
    1
