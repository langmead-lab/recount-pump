#!/bin/bash -l

# BTL: as of 11/28/2018 this doesn't work when submitted to slurm;
# error message is "You must install squashfs-tools to build images"

#SBATCH
#SBATCH --partition=shared
#SBATCH --nodes=1
#SBATCH --mem=1G
#SBATCH --time=1:00:00
#SBATCH --ntasks-per-node=1

d=/scratch/users/blangme2@jhu.edu/git/recount-pump

python ${d}/src/cluster.py prepare \
    --ini-base ${d}/projects/human2k/creds \
    --cluster-ini ~/.recount/cluster-shared.ini \
    1
