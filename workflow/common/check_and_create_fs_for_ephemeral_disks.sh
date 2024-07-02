#!/usr/bin/env bash
set -exo pipefail

#avoids having to parcel up the available local ssd space
make1FS=$1
#do the following: a) skip loop devices b) find device with root partition (e.g. nvme0n1), get its device name
root=$(lsblk | tail -n+2 | egrep -v -e '^loop' | fgrep " part /" | perl -ne 'chomp; $f=$_; $f=~/^......([^\s]+)p\d/; $n=$1; print "$n\n";')
i=1
#skip loop and root devices, assume rest are local SSDs, assigned to /work$i where $i is from 1-#_of_SSDs
drives=""
num_drives=0
echo -n "" > local_disks.txt
for dev in `lsblk | tail -n+2 | egrep -v -e '^loop' | fgrep -v "$root" | tr -s " " $'\t' | cut -f 1`; do
    if [[ -n $make1FS ]]; then
        drives="${drives} /dev/${dev}"
        num_drives=$((num_drives+1))
    else
        mkfs -q -t ext4 /dev/${dev}
        mkdir -p /work${i} 
        mount /dev/${dev} /work${i}/
        chown -R ubuntu /work${i}
        chmod -R a+rw /work${i}
        echo "/work${i}" >> local_disks.txt
        i=$((i+1))
    fi
done

if [[ -n $make1FS ]]; then
    mdadm --create /dev/md1 --run --force --level=0 --raid-devices=${num_drives} $drives
    mdadm --detail /dev/md1
    mkfs.ext4 -F /dev/md1
    mkdir -p /work1
    mount /dev/md1 /work1
    chown -R ubuntu /work1
    chmod -R a+rw /work1
fi
