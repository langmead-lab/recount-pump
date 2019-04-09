#!/usr/bin/env bash
set -o pipefail -o nounset -o errexit 
#used to make sure there are no ID collisions between multiple annotations when catted together
#expects that you have the path to the gzipped FANTOM-CAT v6 transcripts GTF
#also expects that gffread is in PATH
#http://ccb.jhu.edu/software/stringtie/gff.shtml
#http://ccb.jhu.edu/software/stringtie/dl/gffread-0.9.12.Linux_x86_64.tar.gz

d=$(dirname $0)

g1='G029'
g2='G026'
r1='R109'
f1='F006'

date=`date +%Y%m%d`;

#provide path to FANTOM-CAT 6 transcript annotation
#.e.g /data2/FANTOM/F6_CAT.transcript.gtf.gz
fantomcat6=$1

#download annotations
curl ftp://ftp.ebi.ac.uk/pub/databases/gencode/Gencode_human/release_29/gencode.v29.chr_patch_hapl_scaff.annotation.gtf.gz | zcat > ${g1}
curl ftp://ftp.ebi.ac.uk/pub/databases/gencode/Gencode_human/release_26/gencode.v26.chr_patch_hapl_scaff.annotation.gtf.gz | zcat  > ${g2}
curl ftp://ftp.ncbi.nlm.nih.gov/refseq/H_sapiens/annotation/GRCh38_latest/refseq_identifiers/GRCh38_latest_genomic.gff.gz | zcat > ${r1}.gff
zcat $fantomcat6 > ${f1}

#convert RefSeq GFF->GTF, pick up non-transcript lines & full additional info from the 9th column
gffread ${r1}.gff -T -G -O -o ${r1} 2> ${r1}.gffread.err

for z in ${g1} ${g2} ${r1} ${f1}; do
    cat ${z} | perl -ne 'BEGIN { $tag="'${z}'"; chomp($tag); } chomp; $f=$_; $f=~s/(transcript_id\s+"[^"]+)"/$1.$tag"/; $f=~s/(gene_id\s+"[^"]+)"/$1.$tag"/; print "$f\n";' >> ${z}.gtf
done

#TxDB creation doesn't like CDS intervals in RefSeq, also, every entry needs a gene_id before the gene_name
fgrep -v '	CDS	' ${r1}.gtf | perl -ne 'chomp; $f=$_; if($f!~/gene_id/) { $f=~/transcript_id\s+"[^"]+(.\d\d\d)"/; $tag=$1; $f=~s/(gene_name\s+"([^"]+)")/gene_id "$2.$tag"; $1/; } print "$f\n";' > ${r1}.noCDS.all_gene_ids.gtf
#need this to translate RefSeq chromosome accessions
wget ftp://ftp.ncbi.nlm.nih.gov/refseq/H_sapiens/annotation/GRCh38_latest/refseq_identifiers/GRCh38_latest_assembly_report.txt

#need to convert RefSeq chromosome accessions to GRCh38 chromosome names (e.g. chrM)
egrep -v -e '^#' GRCh38_latest_assembly_report.txt | cut -f 5,7,10 | perl -ne 'chomp; $f=$_; $f=~s/\r$//; ($id,$acc,$name)=split(/\t/,$f); $mid=$name; $mid=$id if($name =~ /_/ || $name eq "na"); print "$acc\t$mid\n";' | sort -k2,2 > GRCh38_latest_assembly_report.txt.cut.mapping

cat ${r1}.noCDS.all_gene_ids.gtf | perl -ne 'BEGIN { open(IN,"<GRCh38_latest_assembly_report.txt.cut.mapping"); while($line=<IN>) { chomp($line); ($acc,$id)=split(/\t/,$line); $h{$acc}=$id; } close(IN); } chomp; $f=$_; @f=split(/\t/,$f); $chrm_acc=$f[0]; $nid=$h{$chrm_acc}; $f[0]=$nid; print "".join("\t",@f)."\n";'  > ${r1}.noCDS.all_gene_ids.fixed_chrms.gtf

#get rid of 2nd transcript_id which causes some exons (all in RefSeq) to be removed
cat ${g1}.gtf ${g2}.gtf ${f1}.gtf ${r1}.noCDS.all_gene_ids.fixed_chrms.gtf | sort -t'	' -k1,1 -k4,4n -k5,5n | egrep -v -e '^#' | perl -ne 'chomp; $f=$_; $t2="T1"; if($f=~/(transcript_id\s+"[^"]+";)/) { $t=$1; $f=~s/transcript_id\s+"[^"]+";/$t2/; $f=~s/transcript_id\s+"[^"]+";//g; $f=~s/$t2/$t/; } print "$f\n";' > ${g1}.${g2}.${r1}.${f1}.${date}.gtf

/bin/bash -x ${d}/disjoin_docker.sh ${g1}.${g2}.${r1}.${f1}.${date}.gtf  > ${g1}.${g2}.${r1}.${f1}.${date}.gtf.disjoin.run 2>&1

sort -k1,1 -k2,2n -k3,3n ${g1}.${g2}.${r1}.${f1}.${date}.gtf.bed > ${g1}.${g2}.${r1}.${f1}.${date}.gtf.sorted.bed

python extract_splice_sites.py G029.gtf > G029.gtf.introns

#filter out non-autosomal chromosomes; convert to BED file; sort
egrep -e '^chr' G029.gtf.introns | fgrep -v "chrUn" | sort -k1,1 -k2,2n -k3,3n | perl -ne 'chomp; ($c,$s,$e,$o)=split(/\t/,$_); $s--; print "$c\t$s\t$e\t.\t1\t$o\n";' > G029.gtf.introns.filtered_sorted.bed

#remove any exon segments so we get consituitive introns (and partials)
bedtools subtract -a G029.gtf.introns.filtered_sorted.bed -b ${g1}.${g2}.${r1}.${f1}.${date}.gtf.sorted.bed > G029.gtf.introns.filtered_sorted.exons_removed.bed

sort -k1,1 -k2,2n -k3,3n G029.gtf.introns.filtered_sorted.exons_removed.bed | perl -ne 'chomp; $f=$_; ($c,$s,$e,$n,$t,$o)=split(/\t/,$f); if($pc) { if($c eq $pc && $s < $pe) { $pe=$e if($e > $pe); next; } print "$pc\t$ps\t$pe\t$p\n"; } $pc=$c; $ps=$s; $pe=$e; $p=join("\t",($n,$t,$o)); END { if($pc) { print "$pc\t$ps\t$pe\t$p\n"; }}' > G029.gtf.introns.filtered_sorted.exons_removed.bed.overlaps

cat G029.gtf.introns.filtered_sorted.exons_removed.bed.overlaps ${g1}.${g2}.${r1}.${f1}.${date}.gtf.bed | sort -k1,1 -k2,2n -k3,3n > ${g1}.${g2}.${r1}.${f1}.G029_introns.${date}.sorted.bed
