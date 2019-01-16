#!/bin/bash -l

#SBATCH --job-name=srav1
#SBATCH --partition=skx-normal
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=1
#SBATCH --time=48:00:00
#SBATCH -A TG-DEB180021

d=/work/04265/benbo81/stampede2/git/recount-pump

set -ex

hostname
module load sratoolkit && fastq-dump -X 10 -L info DRR001484

python ${d}/src/cluster.py run \
    --ini-base ${d}/projects/srav1/creds \
    --cluster-ini ~/.recount/cluster-skx.ini \
    1
