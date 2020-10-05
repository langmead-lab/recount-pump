ps -ef | grep vagrant | grep bash | tr -s " " \\t | cut -f 9 | cut -d'/' -f 6 | sort -u | perl -ne 'chomp; $h{$_}=1; END { for $i (1..75) { next if($h{"n$i"} == 1); print "$i "; } print "\n";}'
