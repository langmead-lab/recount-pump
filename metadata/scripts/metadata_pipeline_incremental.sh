#!/usr/bin/env bash
#runs the full metadata fetching & parsing pipeline for SRA

export LC_ALL=C
dir=$(dirname $0)

#submit an organism (e.g. "${orgn}" or "mouse")
orgn=$1
#number of concurrent fetch/filter jobs to run
#probably not more than 10, and more like 3
num_procs=$2
#start date as YYYY/MM/DD, e.g. 2019/10/01 
startdate=$3
#to filter out to make sure we don't overlap with say recount3
#e.g. /path/to/srav3h/samples.tsv
existing_samples=$4
#optional, defaults to 3 (is for SRA based compilations)
existing_samples_study_col=$5

if [[ -z existing_samples_study_col ]]; then
    existing_samples_study_col=3
fi

cut -f $existing_samples_study_col $existing_samples | sort -u | fgrep -v "study" | sed 's/$/\t/' > existing_samples.studies   

orgn_orig=$orgn
orgn=`echo -n "$orgn_orig" | perl -ne '$o=$_; $o=~s/\s+/_/g; print "$o";'`

#python needs to have BioPython installed as it uses Entrez from Bio
#fetch jobs go to fetch_${orgn}.jobs
#parse jobs go to parse_${orgn}.sh (run serially)
python3 $dir/fetch_sra_metadata.py --orgn "$orgn_orig" --xml-path sra_xmls --err-path parse_errs --start-date "$startdate"

parallel -j $num_procs < fetch_${orgn}.jobs > fetch_${orgn}.jobs.run 2>&1

#don't need to run parsing in parallel (fast enough) and we're writing to the same file
#output file is: all_[orgn]_sra.tsv
/bin/bash -x parse_${orgn}.sh > parse_${orgn}.jobs.run 2>&1

#now remove existing studies we already have
fgrep -v -f existing_samples.studies all_${orgn}_sra.tsv > all_${orgn}_sra.filtered.tsv
mv all_${orgn}_sra.tsv all_${orgn}_sra.prefiltered.tsv
ln -fs all_${orgn}_sra.filtered.tsv all_${orgn}_sra.tsv

#this will in parallel filter out scRNA runs inferred by pattern matching
#but keep smartseq as part of the bulk remainder
#output of this command is a list of full SRA metadata for bulk + smartseq
/bin/bash -x $dir/filter_scrna.sh ${orgn} $num_procs > filter_scrna.sh.run 2>&1

#pick up any runs which don't have "transcriptomic" as source but share a study with ones that do
mkdir nontranscriptomic
pushd nontranscriptomic
python $dir/fetch_sra_metadata.py --orgn "$orgn_orig" --xml-path sra_xmls --err-path parse_errs --start-date "$startdate" --non-transcriptomic

/bin/bash -x fetch_${orgn}.jobs
/bin/bash -x parse_${orgn}.sh
cut -f 2 all_${orgn}_sra.tsv | sort -u | sed -e 's/$/\t/' > all_${orgn}_sra.tsv.studies
fgrep -f all_${orgn}_sra.tsv.studies ../all_${orgn}_sra.no_scrna_except_smart.full_studies.tsv | cut -f 2 | sed -e 's/$/\t/' | sort -u > studies_found_in_transcriptomic
fgrep -f studies_found_in_transcriptomic all_${orgn}_sra.tsv > all_${orgn}_sra.tsv.in_transcriptomic
cat ../all_${orgn}_sra.no_scrna_except_smart.full_studies.tsv all_${orgn}_sra.tsv.in_transcriptomic | sort -u > ../all_${orgn}_sra.no_scrna_except_smart.full_studies_with_nontranscriptomic_runs.tsv
popd
ln -fs all_${orgn}_sra.no_scrna_except_smart.full_studies_with_nontranscriptomic_runs.tsv all.runs.tsv

#get study level info
cut -f 2,8-10 all.runs.tsv | sort -u > all.runs.tsv.study_level
