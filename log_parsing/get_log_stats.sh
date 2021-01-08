dir=$(dirname $0)

fgrep "using mover to copy outputs from" * | sed 's/:/ /' | sort -k6,6 -k2,4 > all_lines.sorted
cut -d' ' -f 6,16 all_lines.sorted | cut -d'/' -f 1,11 | sed 's/"//g' | sed 's/\///' > all_lines.sorted.nodes_runs
python $dir/parse_stats_from_slurm.py all_lines.sorted > all_lines.sorted.parsed 2>all_lines.sorted.parsed_err
