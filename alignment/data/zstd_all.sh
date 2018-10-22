#!/bin/bash -l
#SBATCH
#SBATCH --partition=shared
#SBATCH --nodes=1
#SBATCH --mem=1G
#SBATCH --time=4:00:00
#SBATCH --ntasks-per-node=1

# Shared queue:
# --ntasks-per-node=(default: 1, max: 24)
# --mem=(default: 5G, max: 128G)
# --time=(default: 1:00:00, max: 100:00:00)

for i in *.fastq ; do
    zstd $i -o $i.zst
done
