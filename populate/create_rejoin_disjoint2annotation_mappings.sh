#e.g. G029.G026.R109.F006.20190220.gtf w/ ERCC & SIRV transcripts
ORIG_UNIONED_GTF=$1

root=$(dirname $0)

#run recount-pump/populate/docker_disjoin.sh first on the original GTF file
mv $ORIG_UNIONED_GTF ${ORIG_UNIONED_GTF}.original
cat ${ORIG_UNIONED_GTF}.original | perl -ne 'chomp; $f=$_; @f=split(/\t/,$f); if($f[2] eq "exon") { $info=$f[8]; $info=~/exon_id\s+"([^"]+)/; $eid=$1; if(!$eid) { $info=~/gene_id\s+"([^"]+)/; $eid=$1; if(!$eid) { print STDERR "NO_EXON_NO_GENE_IDS\t$f\n"; continue; }} ($c,$s,$e,$o)=($f[0],$f[3],$f[4],$f[6]); $f[8]=~s/exon_id\s+"([^"]+)";?//; $f[8]="exon_id \"$eid|$c|$s|$e|$o\"; ".$f[8]; $f=join("\t",@f); } print "$f\n";' > $ORIG_UNIONED_GTF

/bin/bash -x $root/disjoin_docker.sh $ORIG_UNIONED_GTF

#the previous script will copy the original input file into the current dir
#and will output the results to the current dir with a bed suffix regardless of the actual file format
ORIG_UNIONED_GTF=$(basename $ORIG_UNIONED_GTF)
mv ${ORIG_UNIONED_GTF}.bed ${ORIG_UNIONED_GTF}.gff

#extract the disjoint exons with gene IDs as a BED file, ${ORIG_UNIONED_GTF}.bed.gff is produced by the disjoin.R script
fgrep -v "##" ${ORIG_UNIONED_GTF}.gff | perl -ne 'chomp; $f=$_; @f=split(/\t/,$f); $f[3]--; print "".join("\t",@f)."\n";'  | sort -t'	' -k1,1 -k4,4n -k5,5n > ${ORIG_UNIONED_GTF}.gff.bed.sorted

##########Gene Mapping

#get gene coords
#this gets the largest coordinate range for each gene w/o resorting to subselecting by type (since for certain single exon genes that can be nuanced)
#i.e. if "gene" and/or "exon" are used as type filters, some genes/exons will be missed
cut -f 1,4,5,7,9 ${ORIG_UNIONED_GTF} | perl -ne 'chomp; ($c,$s,$e,$o,$ginfo)=split(/\t/,$_); $s--; $ginfo=~/gene_id\s+"([^"]+)/; $g=$1; if($h{$g} && $h{$g}->[2] ne $c) { $h{$g}->[4]=1; $g.=".$c"; } $h{$g}->[0]=$s if(!$h{$g}->[0] || $h{$g}->[0] > $s); $h{$g}->[1]=$e if(!$h{$g}->[1] || $h{$g}->[1] < $e); $h{$g}->[2]=$c; $h{$g}->[3]=$o; END { for $g (keys %h) { @a=@{$h{$g}}; if(scalar(@a) > 4) { $g.=".".$a[2]; } print "".join("\t",$a[2],$a[0],$a[1],$g,"0",$a[3],"2")."\n";}}' > ${ORIG_UNIONED_GTF}.gene_coords.bed

#now produce the disjoint exon2annotated gene mapping file for rejoining to get annotated gene counts from disjoint exon counts
cat ${ORIG_UNIONED_GTF}.gene_coords.bed ${ORIG_UNIONED_GTF}.gff.bed.sorted | perl -ne 'chomp; $f=$_; @f=split(/\t/,$f); $gid=$f[3]; if($f[6] eq "2") { $h{$gid}=$f; next; } $f=join("\t",@f); ($c,$s,$e,$o,$info)=($f[0],$f[3],$f[4],$f[6],$f[8]); $info=~/gene_id=([^;]+)/; $gs=$1; $info=~/exon_name=([^;]+)/; $es=$1; @genes=split(/,/,$gs); for $g (@genes) { $ginfo=$h{$g}; if(!$ginfo) { $ginfo=$h{$g.".$c"}; } print "$c\t$s\t$e\t.\t0\t$o\t$ginfo\n"; }' | sort -t'	' -k1,1 -k2,2n -k3,3n > ${ORIG_UNIONED_GTF}.disjoint2exons2genes.bed

#calculate the per gene (in a specific annotation) base pair length (counting only disjoint exon lengths)
cat ${ORIG_UNIONED_GTF}.disjoint2exons2genes.bed | perl -ne 'chomp; $f=$_; @f=split(/\t/,$f); ($s,$e,$g)=($f[1],$f[2],$f[9]); $h{$g}+=($e-$s); END { for $g_ (keys %h) { print "$g_\t".$h{$g_}."\n"; }}' | sort -k1,1 > ${ORIG_UNIONED_GTF}.disjoint2exons2genes.bed.gene_bpl.tsv


##########Exon Mapping

#get exon coords, this time we have to select by exons
#BE VERY CAREFUL that the input GTF has a clear "exon" type label for every exon you have in your disjoint set!
#this is true for G029.G026.R109.F006.20190220.gtf, but isn't for gencodev25 (recount2)

#get disjoint2annotated exon mapping, assumes that the original unioned GTF file used the full pattern (exon/gene_name|chr|start|end|strand) as the exon_id
#we'll use this to get the proper mapping back
cat ${ORIG_UNIONED_GTF}.gff.bed.sorted | perl -ne 'chomp; $f=$_; @f=split(/\t/,$f); $eid=$f[3]; if($f[6] eq "2") { $h{$eid}=$f; next; } $f=join("\t",@f); ($c,$s,$e,$o,$info)=($f[0],$f[3],$f[4],$f[6],$f[8]); $info=~/gene_id=([^;]+)/; $gs=$1; $info=~/exon_name=([^;]+)/; $es=$1; @genes=split(/,/,$gs); @exons=@genes; if($es) { @exons=split(/,/,$es); } for $ex (@exons) { ($ename,$c2,$s2,$e2,$o2)=split(/\|/,$ex); $s2--; print "$c\t$s\t$e\t.\t0\t$o\t$c2\t$s2\t$e2\t$ename\t0\t$o2\t2\n"; }' 2> ${ORIG_UNIONED_GTF}.disjoint2exons.bed.err | sort -t'	' -k1,1 -k2,2n -k3,3n > ${ORIG_UNIONED_GTF}.disjoint2exons.bed

#get exonID2geneIDs mapping
cat ${ORIG_UNIONED_GTF}.disjoint2exons.bed | perl -ne 'BEGIN { open(IN,"<'${ORIG_UNIONED_GTF}'.disjoint2exons2genes.bed"); while($line=<IN>) { chomp($line); @f=split(/\t/,$line); ($c,$s,$e)=@f; $o=$f[5]; $k=join("\t",($c,$s,$e,$o)); $h{$k}.=$f[9].";"; } close(IN); } chomp; @f=split(/\t/,$_); ($c,$s,$e)=@f; $o=$f[5]; $k=join("\t",($c,$s,$e,$o)); $gids=$h{$k}; $h2{$f[9]}.="$gids"; END { for $e (keys %h2) { print "$e\t".$h2{$e}."\n";}}' > ${ORIG_UNIONED_GTF}.exonIDs2geneIDs.tsv

#then get exonID2annotation mapping from previous file
cat ${ORIG_UNIONED_GTF}.exonIDs2geneIDs.tsv | perl -ne 'chomp; ($eid,$gids)=split(/\t/,$_); @gids=split(/;/,$gids); %h=map { $_=~/\.([^\.]{4})$/; $p=$1; $p=>1; } @gids; print "$eid\t".join(",",keys %h)."\n";' > ${ORIG_UNIONED_GTF}.exonIDs2annotations.tsv

#now get the exons.bed file to be used in the actual pipeline
cut -f 1-6 ${ORIG_UNIONED_GTF}.disjoint2exons.bed | sort -k1,1 -k2,2n -k3,3n | uniq > ${ORIG_UNIONED_GTF}.disjoint_exons.bed

#now add non-exon-overlapping introns for QC/stats
/bin/bash -x ${root}/add_introns.sh ${ORIG_UNIONED_GTF} ${ORIG_UNIONED_GTF}.disjoint_exons.bed
