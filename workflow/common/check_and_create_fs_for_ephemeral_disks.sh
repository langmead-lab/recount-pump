#!/usr/bin/env bash
set -exo pipefail

#do the following: a) skip loop devices b) find device with root partition (e.g. nvme0n1), get its device name
root=$(lsblk | tail -n+2 | egrep -v -e '^loop' | fgrep " part /" | perl -ne 'chomp; $f=$_; $f=~/^......([^\s]+)p\d/; $n=$1; print "$n\n";')
i=1
#skip loop and root devices, assume rest are local SSDs, assigned to /work$i where $i is from 1-#_of_SSDs
echo -n "" > local_disks.txt
for dev in `lsblk | tail -n+2 | egrep -v -e '^loop' | fgrep -v "$root" | tr -s " " $'\t' | cut -f 1`; do
    mkfs -q -t ext4 /dev/${dev}
    mkdir -p /work${i} 
    mount /dev/${dev} /work${i}/
    chown -R ubuntu /work${i}
    chmod -R a+rw /work${i}
    echo "/work${i}" >> local_disks.txt
    i=$((i+1))
done
