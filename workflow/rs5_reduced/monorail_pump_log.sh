#!/usr/bin/env bash
#set -exo pipefail
export MD_IP=169.254.169.254
export LOG_GROUP="monorail-pump"
export LOG_STREAM="pump_runs"
run=$1
study=$2
mode=$3
REGION=$4
rdir=$5
if [[ -z $REGION ]]; then
    export REGION="us-east-1"
fi
#checkpoint OR path2fastqfiles,
#checkpoint is one of:
#+) START
#+) STAR_DONE
#+) INDEX_DONE
#+) BAMCOUNT_DONE
#+) PUMP_FAILED
#+) PUMP_DONE (before copy back to S3)
#+) END (after copy back to S3)
#if path2fastqfiles, files are checked for a  small sample of reads to see if there's evidence of true scRNA (chromium/10x/droplet)
#also paired status and read length in both reads1 and reads2 files are logged

#need to establish a unique ID for this instance of processing this RUN accession through pump:
#date.run_acc.study_acc.node_ip
DATE=$(date +"%Y%m%dT%H%M%S%z")
if [[ ! -e /dev/shm/INSTANCE_INFO ]]; then
    IP=$(curl http://${MD_IP}/latest/meta-data/local-ipv4)
    itype=$(curl http://${MD_IP}/latest/meta-data/instance-type)
    #IP=$(echo "$IP" | sed 's#\.#-#g')
else
    instance_info=$(cat /dev/shm/INSTANCE_INFO)
    IP=$(echo "$instance_info" | cut -d';' -f1)
    itype=$(echo "$instance_info" | cut -d';' -f2)
fi
JOB_ID="${run}|${study}"

#TODO2:
#make 1 call to get: a) IP address annd b) instance type at init, then write to /dev/shm and have all workers read from that
#then every message will have ID, itype, mode, cores, memory, disk space, load average

rdir=$(dirname $mode)
#fastqfiles mode:
if [[ $rdir =~ "/" ]]; then
    echo "logging FASTQ stats"
    exit 0
fi

#collect additional stats from machine
#disk usage
df=$(df -h | tr -s " " $'|' | cut -d'|' -f 4,5,6 | tail -n+2 | fgrep -v "|/snap/" | fgrep -v "|/run" | fgrep -v "|/sys" | fgrep -v "|/dev" | tr $'\n' ";" | sed 's#;$#\n#')
ncores=$(fgrep -i processor /proc/cpuinfo  | wc -l) 
ram=$(head -3 /proc/meminfo | tr $'\n' ";" | sed 's# ##g' | sed 's#;$#\n#')
load_avg=$(top -b -n  1  | awk '/load average/ { printf "%s\n", $12 }' | sed 's#,##')

#now log:
entry="${DATE};${mode};${JOB_ID};${IP};${itype};${ncores};${load_avg};${ram};${df}"
echo "$entry"
d2=$(($(date +%s)*1000))
if [[ "$mode" == "$PUMP_FAILED" ]]; then
    standardout=$(cat $rdir/std.out | sed 's#;#,#g' | tr $'\n' ";")
    entry="${entry}|||${standardout}"
    aws logs put-log-events --region $REGION --log-group-name $LOG_GROUP --log-stream-name $LOG_STREAM --log-events "timestamp=${d2},message=${entry}"
else    
    aws logs put-log-events --region $REGION --log-group-name $LOG_GROUP --log-stream-name $LOG_STREAM --log-events "timestamp=${d2},message=${entry}"
fi
