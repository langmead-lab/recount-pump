#!/usr/bin/env bash
#list of scRNA tech taken from here:
#https://www.frontiersin.org/files/Articles/441123/fgene-10-00317-HTML/image_m/fgene-10-00317-t001.jpg

#organism, assumes all_${orgn}_sra.tsv already exists in the current working directory
orgn=$1
#number of concurrent filtering processes
#5-10
num_procs=$2

echo -n "" > filter_scrna.${orgn}.jobs
for t in 'single.?cell' 'seq.?well' 'smart.?seq' 'quartz.?seq' 'super.?seq' 'matq.?seq' 'strt.?seq' 'cel.?seq' 'mars.?seq' 'drop.?seq' 'split.?seq' 'sci-rna.?seq' 'dronc.?seq'; do 
    name=`perl -e '$t="'$t'"; $t=~s/[\.\?\s\+]+/_/; print "$t\n";'`
    echo "egrep -ie '${t}' all_${orgn}_sra.tsv > all_${orgn}_sra.${name}" >> filter_scrna.${orgn}.jobs
done

#additional single cell pattern matching (allow multiple spaces between "single" and "cell")
echo "egrep -ie 'single +cell' all_${orgn}_sra.tsv > all_${orgn}_sra.single_cell2" >> filter_scrna.${orgn}.jobs

for t in "scrna" "10x" "chromium" "fluidigm" "indrop" "ctyoseq"; do
    echo "fgrep -i '${t}' all_${orgn}_sra.tsv > all_${orgn}_sra.${t}" >> filter_scrna.${orgn}.jobs
done

#need to call out one study which matches STRT-seq like pattern by is actually CAGE-seq (5' capture in bulk)
echo "fgrep -i ' strt ' all_human_sra.tsv | fgrep -v 'SRP116908' > all_${orgn}_sra.strt_seq2" >> filter_scrna.${orgn}.jobs

parallel -j $num_procs < filter_scrna.${orgn}.jobs > filter_scrna.${orgn}.jobs.run 2>&1
#merge multiple outputs for: 10x; strt-seq, and single-cell
mv all_${orgn}_sra.chromium all_${orgn}_sra.10x2
for t in "10x" "strt_seq" "single_cell"; do
    cat all_${orgn}_sra.${t} all_${orgn}_sra.${t}2 | sort -u > all_${orgn}_sra.${t}.sorted
    mv all_${orgn}_sra.${t}.sorted all_${orgn}_sra.${t}
    rm all_${orgn}_sra.${t}2
done

#one study is the "viscRNA-seq" method but gets caught by our smartseq pattern
fgrep "SRP152576" all_${orgn}_sra.smart_seq > all_${orgn}_sra.visc_seq
fgrep -v "SRP152576" all_${orgn}_sra.smart_seq > all_${orgn}_sra.smart_seq_
mv all_${orgn}_sra.smart_seq_ all_${orgn}_sra.smart_seq

#get final list of SRRs, per scRNA tech. as well as overall
echo -n "" > all_scrnas.all_${orgn}_sra.tsv.srrs_
for f in `ls all_${orgn}_sra.*`; do cut -f 1 $f | sort -u | perl -ne 'chomp; print "$_\t\n";' > ${f}.srr ;  cat ${f}.srr >> all_scrnas.all_${orgn}_sra.tsv.srrs_ ; done
sort -u all_scrnas.all_${orgn}_sra.tsv.srrs_ | perl -ne 'chomp; print "$_\t\n";' > all_scrnas.all_${orgn}_sra.tsv.srrs
rm all_scrnas.all_${orgn}_sra.tsv.srrs_

#now get final lists of SRRs & complete metadata
fgrep -v -f all_${orgn}_sra.smart_seq.srr all_scrnas.all_${orgn}_sra.tsv.srrs > all_scrnas_except_smart.all_${orgn}_sra.tsv.srrs
#allow smartseq to be kept with the rest of the bulk runs
fgrep -v -f all_scrnas_except_smart.all_${orgn}_sra.tsv.srrs all_${orgn}_sra.tsv > all_${orgn}_sra.no_scrna_except_smart.tsv
#finally get list of full metadata for just scRNA (w/o smartseq)
fgrep -f all_scrnas_except_smart.all_${orgn}_sra.tsv.srrs all_${orgn}_sra.tsv > all_${orgn}_sra.scrna_except_smart.tsv
