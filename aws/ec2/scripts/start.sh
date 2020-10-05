s=$(seq $1 $2)
for i in $s; do pushd n${i} ; ../../run_local.sh $i ; popd ; done
