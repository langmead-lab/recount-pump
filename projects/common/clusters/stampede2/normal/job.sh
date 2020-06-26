#!/bin/bash -l
#SBATCH --partition=normal
#SBATCH --job-name=rc-knl
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=1
#SBATCH --time=48:00:00
#SBATCH -A TG-DEB180021

tranche=sra_human_v3_10
auto_globus=

#use this if running automated globus transfers
if [[ -n "$auto_globus" ]]; then
    rdelay=`perl -e 'print "".int(rand(360));'`
    sleep $rdelay
fi

module load tacc-singularity
umask 0077
LD_PRELOAD=/work/00410/huang/share/patch/myopen.so ~/miniconda2/bin/python /work/04620/cwilks/stampede2/git/recount-pump/src/cluster.py run --ini-base creds --cluster-ini creds/cluster-normal.ini $tranche
