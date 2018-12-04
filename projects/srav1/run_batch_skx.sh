#!/bin/bash -l

#SBATCH --job-name=geuv
#SBATCH --partition=skx-normal
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=1
#SBATCH --time=48:00:00
#SBATCH -A TG-CIE170020

d=/work/04265/benbo81/stampede2/git/recount-pump

python ${d}/src/cluster.py run \
    --ini-base ${d}/projects/srav1/creds \
    --cluster-ini ~/.recount/cluster-skx.ini \
    1
