#e.g. tranche manifest txt file with format: STUDY<SPACE>RUN
list_file=$1
#number of parallel processes to download 1 read FASTQs
num_procs=$2

export LC_ALL=C
rm -rf /dev/shm/prechecks*
mkdir -p /dev/shm/prechecks
mkdir -p /dev/shm/prechecks.stdout
mkdir -p /dev/shm/prechecks.stderr
cut -d' ' -f 2 $list_file | sort -u | perl -ne 'chomp; print "fastq-dump -N 1 -X 1 -O /dev/shm/prechecks $_ > /dev/shm/prechecks.stdout/$_ 2> /dev/shm/prechecks.stderr/$_\n";' > runs.precheck

parallel -j $num_procs < runs.precheck
