#!/bin/bash -l

#SBATCH
#SBATCH --partition=shared
#SBATCH --nodes=1
#SBATCH --mem=1G
#SBATCH --time=1:00:00
#SBATCH --ntasks-per-node=1

STUDY=
d=/scratch/users/blangme2@jhu.edu/git/recount-pump

python ${d}/src/cluster.py prepare \
    --ini-base ${d}/projects/srav1/creds \
    --cluster-ini ~/.recount/cluster-shared.ini \
    1
