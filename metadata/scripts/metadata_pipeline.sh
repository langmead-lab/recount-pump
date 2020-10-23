#!/usr/bin/env bash
#runs the full metadata fetching & parsing pipeline for SRA

#submit an organism (e.g. "${orgn}" or "mouse")
orgn=$1
#number of concurrent fetch/filter jobs to run
#probably not more than 10, and more like 5
num_procs=$2

orgn_orig=$orgn
orgn=`echo -n "$orgn_orig" | perl -ne '$o=$_; $o=~s/ /_/g; print "$o";'`

#python needs to have BioPython installed as it uses Entrez from Bio
#fetch jobs go to fetch_${orgn}.jobs
#parse jobs go to parse_${orgn}.sh (run serially)
mkdir -p sra_xmls
mkdir -p parse_errs
python fetch_sra_metadata.py "$orgn_orig" $orgn sra_xmls parse_errs

#parallel -j $num_procs < fetch_${orgn}.jobs > fetch_${orgn}.jobs.run 2>&1
parallel -j 3 < fetch_${orgn}.jobs > fetch_${orgn}.jobs.run 2>&1
#/usr/bin/time -v /bin/bash -x fetch_${orgn}.jobs > fetch_${orgn}.jobs.run 2>&1

#don't need to run parsing in parallel (fast enough) and we're writing to the same file
#output file is: all_[orgn]_sra.tsv
/bin/bash -x parse_${orgn}.sh > parse_${orgn}.jobs.run 2>&1

#this will in parallel filter out scRNA runs inferred by pattern matching
#but keep smartseq as part of the bulk remainder
#output of this command is a list of full SRA metadata for bulk + smartseq
/bin/bash -x filter_scrna.sh ${orgn} $num_procs > filter_scrna.sh.run 2>&1

#pick up any runs which don't have "transcriptomic" as source but share a study with ones that do
mkdir nontranscriptomic
pushd nontranscriptomic
mkdir sra_xmls
mkdir parse_errs
python ../fetch_sra_metadata.py "$orgn_orig" $orgn sra_xmls parse_errs 1
/bin/bash -x fetch_${orgn}.jobs
/bin/bash -x parse_${orgn}.sh
cut -f 2 all_${orgn}_sra.tsv | sort -u | sed -e 's/$/\t/' > all_${orgn}_sra.tsv.studies
fgrep -f all_${orgn}_sra.tsv.studies ../all_${orgn}_sra.no_scrna_except_smart.full_studies.tsv | cut -f 2 | sed -e 's/$/\t/' | sort -u > studies_found_in_transcriptomic
fgrep -f studies_found_in_transcriptomic all_${orgn}_sra.tsv > all_${orgn}_sra.tsv.in_transcriptomic
cat ../all_${orgn}_sra.no_scrna_except_smart.full_studies.tsv all_${orgn}_sra.tsv.in_transcriptomic | sort -u > ../all_${orgn}_sra.no_scrna_except_smart.full_studies_with_nontranscriptomic_runs.tsv
popd
ln -fs all_${orgn}_sra.no_scrna_except_smart.full_studies_with_nontranscriptomic_runs.tsv all.runs.tsv
