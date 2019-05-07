#list of scRNA tech taken from here:
#https://www.frontiersin.org/files/Articles/441123/fgene-10-00317-HTML/image_m/fgene-10-00317-t001.jpg

parallel -j 5 < scrna_filter.jobs > scrna_filter.jobs.run 2>&1

echo -n "" > all_scrnas.all_human_sra.tsv.srrs_
for f in `ls all_human_sra.tsv.*`; do cut -f 1 $f | sort -u | perl -ne 'chomp; print "$_\t\n";' > ${f}.srr ;  cat ${f}.srr >> all_scrnas.all_human_sra.tsv.srrs_ ; done
sort -u all_scrnas.all_human_sra.tsv.srrs_ | perl -ne 'chomp; print "$_\t\n";' > all_scrnas.all_human_sra.tsv.srrs
rm all_scrnas.all_human_sra.tsv.srrs_

fgrep -v -f all_human_sra.tsv.scrna.smart.seq.srr all_scrnas.all_human_sra.tsv.srrs > all_scrnas_except_smart.all_human_sra.tsv.srrs
