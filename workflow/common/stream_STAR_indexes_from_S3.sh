#!/usr/bin/env bash
set -exo pipefail
#assume STAR is in the path
export STAR=STAR
#e.g. s3://path/to/ref/hg38/star_idx_directory
#s3://recount-ref
S3prefix=$1
#hg38 or grcm38
ref=$2
export S3path="$S3prefix/$ref"
#e.g. /path/to/ref/hg38
outDir=$3

if [[ -z $outDir ]]; then
    outDir="."
else
    mkdir -p $outDir
fi
pushd $outDir

echo -n "" > download.jobs
echo -n "" > untar.jobs
for f in salmon_index unmapped_hisat2_idx gtf fasta; do
    echo "aws s3 cp $S3path/${f}.tar.gz ./" >> download.jobs
    echo "tar -zxvf ${f}.tar.gz" >> untar.jobs
done
echo "/usr/bin/time -v parallel -j8 < download.jobs > download.jobs.run8 2>&1" > other.jobs
echo "/usr/bin/time -v parallel -j8 < untar.jobs > untar.jobs.run8 2>&1" >> other.jobs

/usr/bin/time -v /bin/bash -x other.jobs > other.jobs.run1 2>&1 &

#copy down fully the small text files for the genome index---this is fast
for f in `aws s3 ls $S3path/star_idx/ | tr -s " " $'\t' | cut -f 4 | fgrep ".txt"`; do
    rm -f $outDir/$f
    aws s3 cp $S3path/star_idx/$f $outDir/$f
done

#first remove any shared memory segments
#asssume we're the only shared-mem game in town
ipcrm --all
#for idx in `ipcs | egrep -e '^0x' | tr -s " " $'\t' | cut -f 2`; do
#    ipcrm -m $idx
#done

#now steam to a FIFO file the really large genome index files in the background
for f in `aws s3 ls $S3path/star_idx/ | tr -s " " $'\t' | cut -f 4 | fgrep -v ".txt"`; do
    rm -f $outDir/$f
    mkfifo $outDir/$f
    aws s3 cp $S3path/star_idx/$f - > $outDir/$f &
done
#then run STAR load, loads genome and then exits (if successful) leaving genome loaded for other runs
$STAR --genomeLoad LoadAndExit --genomeDir $outDir
popd
echo "DONE"
