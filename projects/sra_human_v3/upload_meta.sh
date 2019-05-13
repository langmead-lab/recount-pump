#!/bin/bash

set -e

superstudy=sra_human_v3
taxon_id=9606

for i in by_run_w_overlaps/tranche_?.txt ; do
    cat $i | gzip > ${i}.gz
    aws --profile jhu-langmead s3 cp \
        ${i}.gz s3://recount-pump-experiments/${superstudy}/${i}.gz
done

#upload the original XMLs from the SRA search output
aws --profile jhu-langmead s3 cp all_human_9606_rnaseq_transcriptomic_illumina_public.raw_xmls.20190503.tar.gz s3://recount-pump-experiments/${superstudy}/
#upload the converted to TSV version of the metadata from the raw XMLs in the previous file
aws --profile jhu-langmead s3 cp all_human_9606_rnaseq_transcriptomic_illumina_public.converted_from_xml.20190503.tsv.gz s3://recount-pump-experiments/${superstudy}/
