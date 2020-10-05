#find . -name "*.log" -exec cat {} > all_logs \;
logs=all_logs

#fgrep "using mover to copy outputs from" $logs | sed 's/:/ /' | sed 's/default://' | sed 's/ \+/ /g;' | sort -k2,4 > all_lines.sorted
fgrep "using mover to copy outputs from" $logs | sed 's/:/ /' | sed 's/^ \+default \+//' | sed 's/ \+/ /g;' | sort -k1,3 > all_lines.sorted
cut -d' ' -f 6,16 all_lines.sorted | cut -d'/' -f 1,8 | sed 's/"//g' | sed 's/\///' | sed 's/s3://' > all_lines.sorted.nodes_runs

#get bytes total for runs attempted
fgrep "got job" $logs | cut -d',' -f 4 | sort -u | sed 's/$/\t/' > all_logs.attempted_runs
fgrep -f all_logs.attempted_runs snaptronV2/srav1m/samples.tsv | cut -f 32 | numsum

#get bytes total for runs finished
cut -d' ' -f 2 all_lines.sorted.nodes_runs | sort -u | sed 's/$/\t/' > all_lines.sorted.nodes_runs.runs
fgrep -f all_lines.sorted.nodes_runs.runs snaptronV2/srav1m/samples.tsv | cut -f 32 | numsum
