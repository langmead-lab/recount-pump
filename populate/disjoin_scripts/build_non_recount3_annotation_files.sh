#!/usr/bin/env bash
set -exo pipefail

#should have 1) original full GTF (genes, exons, etc...) 2) ERCC and SIRV spike in annotations 3) exons should have the exon_id set to the recount_id: "chromosome|start|end|strand" format
#e.g. mouse.gencodeM23.genes.subset.ercc_sirv.gtf
original_unioned_gtf=$1

#e.g. mouse
genome_common=$2

#e.g. M023
annotation_short=$3

#tab-delimited list of gene_ids and the sum of the exon spans which make up the gene (not the full coordinate span of the gene itself)
#useful in recount3 for scaling/normalization
#e.g. *disjoint2exons2genes.bed.gene_bpl.tsv
gene_bp_lengths=$4

#raw original annotation GTF to get headers
#.e.g Rattus_norvegicus.mRatBN7.2.105.gtf
original_gtf=$5

#for both genes and exons we want to get the original GTF annotation *but in the same order as in the recount-ready coverage matrices*
#additionally for exons we want to add the recount_exon_id to the GTF for matching purposes in recount3

##gene
#prepare to skip headers in the later perl script, but get the original ones now
set +o pipefail
num_header_lines_=$(cat $original_gtf | fgrep -v -m1 -n "#" | cut -d':' -f1)
num_header_lines=$((num_header_lines_ - 1))
cat $original_gtf | head -${num_header_lines} > ${genome_common}.gene_sums.${annotation_short}.gtf
set -o pipefail

fgrep -v $'\tERCC\t' $original_unioned_gtf | fgrep -v $'\tLexogenSIRVData\t' | fgrep $'\tgene\t' | perl -ne 'BEGIN { open(IN,"'$gene_bp_lengths'"); while($line=<IN>) { chomp($line); ($gid,$ln)=split(/\t/,$line,-1); $glens{$gid}=$ln; } close(IN); } chomp; $f=$_; @f=split(/\t/,$f,-1); $f=~/gene_id\s+"([^;]+)";/; $k=$1; $glen=$glens{$k}; if(!$glen) { die "missing gene bp length for $k\n";} $f[5]=$glen; $line=join("\t",@f); print "$line\n";' >> ${genome_common}.gene_sums.${annotation_short}.gtf
gzip -f ${genome_common}.gene_sums.${annotation_short}.gtf

##exon
#prepare to skip headers in the later perl script, but get the original ones now
set +o pipefail
num_header_lines_=$(cat $original_gtf | fgrep -v -m1 -n "#" | cut -d':' -f1)
num_header_lines=$((num_header_lines_ - 1))
cat $original_gtf | head -${num_header_lines} > ${genome_common}.exon_sums.${annotation_short}.gtf
set -o pipefail

#this removes the combo recount_id + ensembl exon_id as the exon_id and just uses the ensembl exon_id
fgrep -v $'\tERCC\t' $original_unioned_gtf | fgrep -v $'\tLexogenSIRVData\t' | fgrep $'\texon\t' | perl -ne 'chomp; $f=$_; @f=split(/\t/,$f,-1); $f=~s/(exon_id\s+"[^\|]+)\|[^\|]+\|[^\|]+\|[^\|]+\|[+-]";/$1";/; $k=join("|",($f[0],$f[3],$f[4],$f[6])); $line=$f." recount_exon_id \"$k\";"; print "$line\n";' >> ${genome_common}.exon_sums.${annotation_short}.gtf
gzip -f ${genome_common}.exon_sums.${annotation_short}.gtf
