#!/usr/bin/env bash
set -exo pipefail
#download and re-assemble split-up version of STAR index for a given organism's ref
#along with the other annotation/fasta files from the *reduced* set of recount3/Monorail indexes (no Salmon/Hisat)

ref=$1

mkdir -p $ref
pushd $ref
mkdir -p star_idx
#retrieve split up star index files in parallel
prefix="https://recount-ref.s3.amazonaws.com/$ref"

for i in {0..19}; do i0=0; if [[ $i -gt 9 ]]; then i0=""; fi ; echo "aws s3 cp s3://monorail-batch/faster_refs/$ref/star_idx/SA${i0}${i} ./star_idx/"; done > s3dn.jobs
for i in {0..2}; do echo "aws s3 cp s3://monorail-batch/faster_refs/$ref/star_idx/Genome0${i} ./star_idx/"; done >> s3dn.jobs
echo "aws s3 cp s3://monorail-batch/faster_refs/$ref/star_idx/SAindex ./star_idx/" >> s3dn.jobs

echo "cat SA?? > SA" > cat.jobs
echo "cat Genome?? > Genome" >> cat.jobs

echo "curl $prefix/gtf.tar.gz 2> gtf.run | tar -zxvf - 2>> gtf.run" > detar.jobs
echo "curl $prefix/fasta.tar.gz 2> fasta.run | tar -zxvf - 2>> fasta.run" >> detar.jobs

threads=$(cat s3dn.jobs | wc -l)
echo "/usr/bin/time -v parallel -j${threads} < s3dn.jobs > s3dn.jobs.run${threads} 2>&1" > s3dn.sh
echo "pushd star_idx" >> s3dn.sh
echo "/usr/bin/time -v parallel -j2 < ../cat.jobs > ../cat.jobs.run2 2>&1" >> s3dn.sh
echo "rm SA?? Genome??" >> s3dn.sh
echo "aws s3 cp s3://monorail-batch/faster_refs/$ref/star_idx/txtfiles.tar - | tar -xvf -" >> s3dn.sh
echo "popd" >> s3dn.sh
echo "/usr/bin/time -v /bin/bash -x s3dn.sh > s3dn.sh.run1 2>&1" > main.jobs 
echo "/usr/bin/time -v parallel -j2 < detar.jobs > detar.jobs.run2 2>&1" >> main.jobs
/usr/bin/time -v parallel -j2 < main.jobs > main.jobs.run2 2>&1
popd
