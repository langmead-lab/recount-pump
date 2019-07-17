#!/usr/bin/env bash
#create/adds exon_id as original_exon_id|start|end|strand
#e.g. G029.G026.R109.F006.20190220.gtf (original combined form)
GTF=$1

cat ${GTF} | perl -ne 'chomp; $f=$_; @f=split(/\t/,$f); if($f[2] eq "exon") { $info=$f[8]; $info=~/exon_id\s+"([^"]+)/; $eid=$1; if(!$eid) { $info=~/gene_id\s+"([^"]+)/; $eid=$1; if(!$eid) { print STDERR "NO_EXON_NO_GENE_IDS\t$f\n"; continue; }} ($c,$s,$e,$o)=($f[0],$f[3],$f[4],$f[6]); $f[8]=~s/exon_id\s+"([^"]+)";?//; $f[8]="exon_id \"$eid|$c|$s|$e|$o\"; ".$f[8]; $f=join("\t",@f); } print "$f\n";' > ${GTF}.exon_ids 2>${GTF}.lacking_gene_ids

mv ${GTF} ${GTF}.original
mv ${GTF}.exon_ids ${GTF}
