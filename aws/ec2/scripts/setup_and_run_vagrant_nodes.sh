
start=$1
end=$2
s=$(seq $start $end)

for i in $s; do mkdir n${i} ; rsync -av Vagrantfile n${i}/ ; pushd n${i} ; ln -fs /usr/bin/vagrant ; ../run.sh $i ; popd ; done
