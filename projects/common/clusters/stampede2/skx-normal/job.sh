#!/bin/bash -l
#SBATCH --partition=skx-normal
#SBATCH --job-name=short-skx
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=1
#SBATCH --time=12:00:00
#SBATCH -A TG-DEB180021
#SBATCH --exclude=c502-043,c502-001,c478-043,c478-031

tranche=sra_human_v3_10
auto_globus=

#use this if running automated globus transfers
if [[ -n "$auto_globus" ]]; then
    rdelay=`perl -e 'print "".int(rand(360));'`
    sleep $rdelay
fi

module load tacc-singularity
umask 0077
LD_PRELOAD=/work/00410/huang/share/patch/myopen.so ~/miniconda2/bin/python /work/04620/cwilks/stampede2/git/recount-pump/src/cluster.py run --ini-base creds --cluster-ini creds/cluster-skx-normal.ini $tranche
