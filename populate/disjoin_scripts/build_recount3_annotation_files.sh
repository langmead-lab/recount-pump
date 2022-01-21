#!/usr/bin/env bash
set -exo pipefail

#should have 1) original full GTF (genes, exons, etc...) 2) ERCC and SIRV spike in annotations 3) exons should have the exon_id set to the recount_id: "chromosome|start|end|strand" format
#e.g. mouse.gencodeM23.genes.subset.ercc_sirv.gtf
original_unioned_gtf=$1

#e.g. sra.gene_sums.SRP166780.M023.gz
unifier_gene_sums_for_annotation=$2

#e.g. sra.exon_sums.SRP166780.M023.gz
unifier_exon_sums_for_annotation=$3

#e.g. mouse
genome_common=$4

#e.g. M023
annotation_short=$5

#tab-delimited list of gene_ids and the sum of the exon spans which make up the gene (not the full coordinate span of the gene itself)
#useful in recount3 for scaling/normalization
#e.g. *disjoint2exons2genes.bed.gene_bpl.tsv
gene_bp_lengths=$6

#raw original annotation GTF to get headers
#.e.g Rattus_norvegicus.mRatBN7.2.105.gtf.gz
original_gtf=$7

#for both genes and exons we want to get the original GTF annotation *but in the same order as in the recount-ready coverage matrices*
#additionally for exons we want to add the recount_exon_id to the GTF for matching purposes in recount3

##gene
#prepare to skip headers in the later perl script, but get the original ones now
set +o pipefail
num_header_lines_=$(zcat $original_gtf | fgrep -v -m1 -n "#" | cut -d':' -f1)
num_header_lines=$((num_header_lines_ - 1))
zcat $original_gtf | head -${num_header_lines} > ${genome_common}.gene_sums.${annotation_short}.gtf
set -o pipefail

cat <(fgrep -v "ERCC" $original_unioned_gtf | fgrep -v "SIRV" | fgrep $'\tgene\t') <(zcat $unifier_gene_sums_for_annotation | cut -f 1 | fgrep -v "##" | tail -n+2) | perl -ne 'BEGIN { open(IN,"'$gene_bp_lengths'"); while($line=<IN>) { chomp($line); ($gid,$ln)=split(/\t/,$line,-1); $glens{$gid}=$ln; } close(IN); } chomp; $f=$_; @f=split(/\t/,$f); if(scalar(@f) != 1) { @f=split(/\t/,$f,-1); $f=~/gene_id\s+"([^;]+)";/; $k=$1; $glen=$glens{$k}; if(!$glen) { die "missing gene bp length for $k\n";} $f[5]=$glen; $h{$k}=join("\t",@f); next; } $line=$h{$f}; if(!$line) { die "missing row for $f\n"; } print "$line\n";' >> ${genome_common}.gene_sums.${annotation_short}.gtf
gzip -f ${genome_common}.gene_sums.${annotation_short}.gtf

##exon
#prepare to skip headers in the later perl script, but get the original ones now
set +o pipefail
num_header_lines_=$(zcat $original_gtf | fgrep -v -m1 -n "#" | cut -d':' -f1)
num_header_lines=$((num_header_lines_ - 1))
zcat $original_gtf | head -${num_header_lines} > ${genome_common}.exon_sums.${annotation_short}.gtf
set -o pipefail

#this removes the combo recount_id + ensembl exon_id as the exon_id and just uses the ensembl exon_id
cat <(fgrep -v "ERCC" $original_unioned_gtf | fgrep -v "SIRV" | fgrep $'\texon\t') <(zcat $unifier_exon_sums_for_annotation | cut -f 1 | fgrep -v "##" | tail -n+2) | perl -ne 'chomp; $f=$_; @f=split(/\t/,$f); if(scalar(@f) != 1) { $f=~s/(exon_id\s+"[^\|]+)\|[^\|]+\|[^\|]+\|[^\|]+\|[+-]";/$1";/; $k=join("|",($f[0],$f[3],$f[4],$f[6])); $h{$k}=$f." recount_exon_id \"$k\";"; next; } $line=$h{$f}; if(!$line) { die "missing row for $f\n"; } print "$line\n";' >> ${genome_common}.exon_sums.${annotation_short}.gtf
gzip -f ${genome_common}.exon_sums.${annotation_short}.gtf
