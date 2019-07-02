#e.g. G029.G026.R109.F006.20190220.gtf
ORIG_UNIONED_GTF=$1

root=$(dirname $0)

#run recount-pump/populate/docker_disjoin.sh first on the original GTF file
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

##########Exon Mapping

#get exon coords, this time we have to select by exons
#BE VERY CAREFUL that the input GTF has a clear "exon" type label for every exon you have in your disjoint set!
#this is true for G029.G026.R109.F006.20190220.gtf, but isn't for gencodev25 (recount2)

#also some "exons" are the same as they're full gene parents (single line genes) so they wont have exon_ids, in this case use gene_id instead
fgrep '	exon	' ${ORIG_UNIONED_GTF} | cut -f 1,4,5,7,9 | perl -ne 'chomp; ($c,$s,$e,$o,$ginfo)=split(/\t/,$_); $s--; $ginfo=~/gene_id\s+"([^"]+)/; $g=$1; $ginfo=~/exon_id\s+"([^"]+)/; $ex=$1; if(!$ex) { $ex = $g; } print "$c\t$s\t$e\t$ex\t0\t$o\t2\n";' | sort -t'	' -k1,1 -k2,2n -k3,3n -k4,4 -k6,6 | uniq > ${ORIG_UNIONED_GTF}.exon_coords.bed 

#get disjoint2annotated exon mapping
cat ${ORIG_UNIONED_GTF}.exon_coords.bed ${ORIG_UNIONED_GTF}.gff.bed.sorted | perl -ne 'chomp; $f=$_; @f=split(/\t/,$f); $eid=$f[3]; if($f[6] eq "2") { $h{$eid}=$f; next; } $f=join("\t",@f); ($c,$s,$e,$o,$info)=($f[0],$f[3],$f[4],$f[6],$f[8]); $info=~/gene_id=([^;]+)/; $gs=$1; $info=~/exon_name=([^;]+)/; $es=$1; @genes=split(/,/,$gs); @exons=@genes; if($es) { @exons=split(/,/,$es); } for $ex (@exons) { $ginfo=$h{$ex}; print "$c\t$s\t$e\t.\t0\t$o\t$ginfo\n"; }' | sort -t'	' -k1,1 -k2,2n -k3,3n > ${ORIG_UNIONED_GTF}.disjoint2exons.bed
