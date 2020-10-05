#n=`ls n*.log | perl -ne 'chomp; $f=$_; $f=~s/n(.+)\.log/$1/; print "$f\n";'` 
n=`ls n*.log | cut -d'.' -f 1 | tail -n1`
mv *.log ../../done
rsync -av ../Vagrantfile ./
./vagrant up > ${n}b.log 2>&1 &
