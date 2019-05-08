#!/usr/bin/env bash
#runs the full metadata fetching & parsing pipeline for SRA

#submit an organism (e.g. "human" or "mouse")
orgn=$1
#number of concurrent fetch/filter jobs to run
#probably not more than 10, and more like 5
num_procs=$2

#python needs to have BioPython installed as it uses Entrez from Bio
#fetch jobs go to fetch_${orgn}.jobs
#parse jobs go to parse_${orgn}.sh (run serially)
mkdir -p sra_xmls
mkdir -p parse_errs
python fetch_sra_metadata.py $orgn sra_xmls parse_errs

parallel -j $num_procs < fetch_${orgn}_metadata.jobs > fetch_${orgn}_metadata.jobs.run 2>&1

#don't need to run parsing in parallel (fast enough) and we're writing to the same file
#output file is: all_[orgn]_sra.tsv
/bin/bash -x parse_${orgn}_metadata.jobs > parse_${orgn}_metadata.jobs.run 2>&1

#this will in parallel filter out scRNA runs inferred by pattern matching
#but keep smartseq as part of the bulk remainder
#output of this command is a list of full SRA metadata for bulk + smartseq
/bin/bash -x filter_scrna.sh ${orgn} $num_procs > filter_scrna.sh.run 2>&1
