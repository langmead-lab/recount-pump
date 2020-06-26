sra_md_file=$1

for tranche in 0 1 2 3 4 5 6 7 8 9; do
    cp tranche.ini tranche_${tranche}.ini
    sed -i "s/tranche_0.txt/tranche_${tranche}.txt.gz/" tranche_${tranche}.ini
    #run,file size,study columns, make tranches on last run digit
    paste <(cut -f 1,31 ${sra_md_file}) <(cut -f 2 ${sra_md_file}) | egrep -e "${tranche}$" > tranche_${tranche}
    #add in ~1% overlapping studies (shared with one other tranche)
    i=$((tranche+1))
    if [[ $i -eq 10 ]]; then i=0; fi
    paste <(cut -f 1,31 ${sra_md_file}) <(cut -f 2 ${sra_md_file}) | egrep -e "00${i}$" >> tranche_${tranche}
    cut -f 2 tranche_${tranche} | egrep -v -e '^$' | perl -ne 'chomp; $s+=$_; END { print "$s\n";}' > tranche_${tranche}.size
    paste -d' ' <(cut -f 3 tranche_${tranche}) <(cut -f 1 tranche_${tranche}) > tranche_${tranche}.txt
    cat tranche_${tranche}.txt > tranche_${tranche}.txt.gz
    #don't add spike-ins (human + mouse sc & bulk samples) here, they'll be specified in the project.ini file
    #cat ../hm_spike/hm_spike.txt >> ${sra_md_file}_${tranche}.txt
done
