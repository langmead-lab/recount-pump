#!/bin/bash -l

#SBATCH --job-name=srav1
#SBATCH --partition=normal
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=1
#SBATCH --time=48:00:00
#SBATCH --exclude=c410-004,c403-053,c405-001,c411-002,c411-004,c412-064,c412-083,c412-103,c412-104,c413-002,c413-073,c413-081,c411-082,c413-083,c413-092,c415-053,c415-104,c416-012,c416-024,c420-114,c416-041,c407-004,c415-004,c420-102,c416-034,c416-033,c420-103,c420-104,c421-074,c421-094,c410-031,c421-101,c423-034,c406-022,c427-113,c412-003,c416-124,c407-082
#SBATCH -A TG-CIE170020

d=/work/04265/benbo81/stampede2/git/recount-pump

set -ex

hostname
module load sratoolkit && fastq-dump -X 10 -L info DRR001484

python ${d}/src/cluster.py run \
    --ini-base ${d}/projects/srav1/creds \
    --cluster-ini ~/.recount/cluster-knl.ini \
    1
