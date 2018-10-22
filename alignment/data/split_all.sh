#!/bin/bash -l
#SBATCH
#SBATCH --partition=shared
#SBATCH --nodes=1
#SBATCH --mem=1G
#SBATCH --time=8:00:00
#SBATCH --ntasks-per-node=1

# Shared queue:
# --ntasks-per-node=(default: 1, max: 24)
# --mem=(default: 5G, max: 128G)
# --time=(default: 1:00:00, max: 100:00:00)

set -ex

echo 'Splitting Flux FASTQs...'
for SAMPLE in $(cat ../samples.txt) ; do
    if [ ! -f ${SAMPLE}_sim_left.fastq.zst ] ; then
	echo '  Splitting ${SAMPLE}'
	FN=${SAMPLE}_sim.fastq.zst
	[ ! -f ${FN} ] && echo "${FN} does not exist!" && exit 1
	zstd -dc ${FN} |
	    awk '(NR-1) % 8 < 4' | zstd -c -o ${SAMPLE}_sim_left.fastq.zst
	zstd -dc ${FN} |
	    awk '(NR-1) % 8 >= 4' | zstd -c -o ${SAMPLE}_sim_right.fastq.zst
	rm -f ${SAMPLE}_sim.fastq.zst
    fi
done
