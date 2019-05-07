#list of scRNA tech taken from here:
#https://www.frontiersin.org/files/Articles/441123/fgene-10-00317-HTML/image_m/fgene-10-00317-t001.jpg
fgrep -i "scrna" all_human_sra.tsv > all_human_sra.tsv.scrna 
fgrep -i "10x" all_human_sra.tsv > all_human_sra.tsv.10x 
fgrep -i "chromium" all_human_sra.tsv > all_human_sra.tsv.chromium 
fgrep -i "dropseq" all_human_sra.tsv > all_human_sra.tsv.dropseq 
fgrep -i "fluidigm" all_human_sra.tsv > all_human_sra.tsv.fluidigm 
fgrep -i "indrop" all_human_sra.tsv > all_human_sra.tsv.indrop 
fgrep -i "ctyoseq" all_human_sra.tsv > all_human_sra.tsv.cytoseq 
fgrep -i "seq-well" all_human_sra.tsv > all_human_sra.tsv.seq-well 
#known false positive for STRT scRNA needs to be removed here (SRP116908)
fgrep -i " strt " all_human_sra.tsv | fgrep -v "SRP116908" > all_human_sra.tsv.strt
egrep -ie 'smart.seq' all_human_sra.tsv > all_human_sra.tsv.scrna.smart.seq_
fgrep -i 'smartseq' all_human_sra.tsv >> all_human_sra.tsv.scrna.smart.seq_
sort -u all_human_sra.tsv.scrna.smart.seq_ > all_human_sra.tsv.scrna.smart.seq
rm all_human_sra.tsv.scrna.smart.seq_

for t in quartz super matq strt cel mars drop split sci-rna dronc; do fgrep -i "${t}-seq" all_human_sra.tsv > all_human_sra.tsv.${t}-seq ; done

echo -n "" > all_scrnas.all_human_sra.tsv.srrs_
for f in `ls all_human_sra.tsv.*`; do cut -f 1 $f | sort -u | perl -ne 'chomp; print "$_\t\n";' > ${f}.srr ;  cat ${f}.srr >> all_scrnas.all_human_sra.tsv.srrs_ ; done
sort -u all_scrnas.all_human_sra.tsv.srrs_ | perl -ne 'chomp; print "$_\t\n";' > all_scrnas.all_human_sra.tsv.srrs
rm all_scrnas.all_human_sra.tsv.srrs_

fgrep -v -f all_human_sra.tsv.scrna.smart.seq all_scrnas.all_human_sra.tsv.srrs > all_scrnas_except_smart.all_human_sra.tsv.srrs
