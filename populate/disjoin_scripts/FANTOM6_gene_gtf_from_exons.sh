#!/usr/bin/env bash
#produce a GTF for FANTOM6 with gene features rather than just exon features
#using the exon coordinate extents

exon_gtf=$1

cat $exon_gtf | perl -ne 'chomp; $f=$_; ($chrm,$src,$feat,$start,$end,$unused1,$strand,$unused2,$info)=split(/\t/,$f); $info=~/gene_id\s+"([^"]+).F006"/; $gid=$1; push(@{$h{$gid}},[$start,$end]); $h2{$gid}=[$chrm,$strand]; END { for $gid (keys %h) { ($chrm,$strand)=@{$h2{$gid}}; @starts = map { $_->[0]; } @{$h{$gid}}; @ends = map { $_->[1]; } @{$h{$gid}}; @exons = sort { $a <=> $b } (@starts, @ends); ($s,$e) = ($exons[0], $exons[$#exons]); print "$chrm\tFANTOM6\tgene\t$s\t$e\t.\t$strand\t.\tgene_id \"$gid.F006\";\n"; }}' > ${exon_gtf}.genes.gtf
