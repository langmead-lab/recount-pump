#e.g. tranche manifest txt file with format: STUDY<SPACE>RUN
list_file=$1
#number of parallel processes to download 1 read FASTQs
num_procs=$2

#OUT='/dev/shm'
OUT='./'

export LC_ALL=C
rm -rf $OUT/prechecks*
mkdir -p $OUT/prechecks
mkdir -p $OUT/prechecks.stdout
mkdir -p $OUT/prechecks.stderr
cut -d' ' -f 2 $list_file | sort -u | perl -ne 'chomp; print "fastq-dump -N 1 -X 1 -O '$OUT'/prechecks $_ > '$OUT'/prechecks.stdout/$_ 2> '$OUT'/prechecks.stderr/$_\n";' > runs.precheck

parallel -j $num_procs < runs.precheck
