#!/usr//bin/bash
set -o pipefail -o nounset -o errexit
export LC_ALL=C

dir=$(dirname $0)

GTF=$1
EXON_BED=$2
annotation_short=$3

python2 $dir/extract_splice_sites.py ${GTF} > ${GTF}.introns

#create a basic, 1-annotation junction file for now
cat ${GTF}.introns | LC_ALL=C sort -u | perl -ne 'BEGIN { $a='"${annotation_short}"'; $a=lc($a); } chomp; $f=$_; ($c,$s,$e,$o)=split(/\t/,$f,-1); $p0=join("\t",($c,$s,$e)); if(defined($p) && $p eq $p0) { print "$p0\t?\t$a\n"; $p=undef; next; } else { if(defined($p)) { print "$p"."\t$lastsign\t$a\n"; }} $p=$p0; $lastsign=$o; END { if(defined($p)) { print "$p"."\t$lastsign\t$a\n"; }}' | gzip > annotated_junctions.tsv.gz

#filter out non-autosomal chromosomes; convert to BED file; sort
egrep -e '^chr' ${GTF}.introns | fgrep -v "chrUn" | sort -k1,1 -k2,2n -k3,3n | perl -ne 'chomp; ($c,$s,$e,$o)=split(/\t/,$_); $s--; print "$c\t$s\t$e\t.\t1\t$o\n";' > ${GTF}.introns.filtered_sorted.bed

#remove any exon segments so we get consituitive introns (and partials)
bedtools subtract -a ${GTF}.introns.filtered_sorted.bed -b $EXON_BED > ${GTF}.introns.filtered_sorted.exons_removed.bed

sort -k1,1 -k2,2n -k3,3n ${GTF}.introns.filtered_sorted.exons_removed.bed | perl -ne 'chomp; $f=$_; ($c,$s,$e,$n,$t,$o)=split(/\t/,$f); if($pc) { if($c eq $pc && $s < $pe) { $pe=$e if($e > $pe); next; } print "$pc\t$ps\t$pe\t$p\n"; } $pc=$c; $ps=$s; $pe=$e; $p=join("\t",($n,$t,$o)); END { if($pc) { print "$pc\t$ps\t$pe\t$p\n"; }}' > ${GTF}.introns.filtered_sorted.exons_removed.bed.overlaps

cat ${GTF}.introns.filtered_sorted.exons_removed.bed.overlaps $EXON_BED | sort -k1,1 -k2,2n -k3,3n > ${EXON_BED}.w_introns.sorted.bed

cat ${EXON_BED}.w_introns.sorted.bed | perl -ne 'print "0\n";' > blank_exon_sums

echo $'gene\tstart\tend\tname\tscore\tstrand' > exons.w_header.bed
cat ${EXON_BED}.w_introns.sorted.bed >> exons.w_header.bed
pigz --fast -p8 exons.w_header.bed
