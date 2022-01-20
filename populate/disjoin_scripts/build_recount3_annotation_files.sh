#!/usr/bin/env bash
set -exo pipefail

#should have 1) original full GTF (genes, exons, etc...) 2) ERCC and SIRV spike in annotations 3) exons should have the exon_id set to the recount_id: "chromosome|start|end|strand" format
#e.g. mouse.gencodeM23.genes.subset.ercc_sirv.gtf
original_unioned_gtf=$1

#e.g. sra.exon_sums.SRP090980.M023.gz
unifier_exon_sums_for_annotation=$2

#e.g. mouse
genome_common=$3

#e.g. M023
annotation_short=$4

#raw original annotation GTF to get headers
#.e.g Rattus_norvegicus.mRatBN7.2.105.gtf.gz
original_gtf=$5

#this removes the combo recount_id + ensembl exon_id as the exon_id and just uses the ensembl exon_id
set +o pipefail
num_header_lines_=$(zcat $original_gtf | fgrep -v -m1 -n "#" | cut -d':' -f1)
num_header_lines=$((num_header_lines_ - 1))
zcat $original_gtf | head -${num_header_lines} > ${genome_common}.exon_sums.${annotation_short}.gtf
set -o pipefail

cat <(fgrep -v "ERCC" $original_unioned_gtf | fgrep -v "SIRV" | fgrep $'\texon\t') <(zcat $unifier_exon_sums_for_annotation | cut -f 1 | fgrep -v "##" | tail -n+2) | perl -ne 'chomp; $f=$_; @f=split(/\t/,$f); if(scalar(@f) != 1) { $f=~s/(exon_id\s+"[^\|]+)\|[^\|]+\|[^\|]+\|[^\|]+\|[+-]";/$1";/; $k=join("|",($f[0],$f[3],$f[4],$f[6])); $h{$k}=$f." recount_exon_id \"$k\";"; next; } $line=$h{$f}; if(!$line) { print STDERR "missing row for $f\n"; next; } print "$line\n";' >> ${genome_common}.exon_sums.${annotation_short}.gtf
gzip -f ${genome_common}.exon_sums.${annotation_short}.gtf
