#!/bin/bash
#needs to be run as root/sudo
FSXPATH=$1
REGION=$2
if [[ -z $REGION ]]; then
    export REGION="us-east-1"
fi
IP=169.254.169.254
PORT=80
export LOG_GROUP="monorail-pump"
export LOG_STREAM="pump_runs"
#testing IPs and PORTs
#IP=localhost
#IP=10.7.57.255
#PORT=1338
#PORT=9080

cd /

TOKEN=$(curl -s -X PUT "http://${IP}:${PORT}/latest/api/token" -H "X-aws-ec2-metadata-token-ttl-seconds: 21600")
if [ "$?" -ne 0 ]; then
    echo "Error running 'curl' command" >&2
    exit 1
fi

# Periodically check for termination
while sleep 5
do

    HTTP_CODE=$(curl -H "X-aws-ec2-metadata-token: $TOKEN" -s -w %{http_code} -o /dev/null http://${IP}:${PORT}/latest/meta-data/spot/instance-action)

    if [[ "$HTTP_CODE" -eq 401 ]] ; then
        # Refreshing Authentication Token
        TOKEN=$(curl -s -X PUT "http://${IP}:${PORT}/latest/api/token" -H "X-aws-ec2-metadata-token-ttl-seconds: 30")
        continue
    elif [[ "$HTTP_CODE" -ne 200 ]] ; then
        # If the return code is not 200, the instance is not going to be interrupted
        continue
    fi

    echo "Instance is getting terminated..."
    curl -H "X-aws-ec2-metadata-token: $TOKEN" -s http://${IP}:${PORT}/latest/meta-data/spot/instance-action

    DATE=$(date +"%Y%m%dT%H%M%S%z")
    if [[ ! -e /dev/shm/INSTANCE_INFO ]]; then
        IP=$(curl http://${MD_IP}/latest/meta-data/local-ipv4)
        itype=$(curl http://${MD_IP}/latest/meta-data/instance-type)
    else
        instance_info=$(cat /dev/shm/INSTANCE_INFO)
        IP=$(echo "$instance_info" | cut -d';' -f1)
        itype=$(echo "$instance_info" | cut -d';' -f2)
    fi
    #determine which runs are still in process on the machine and log them
    samplesINprocess=$(ls /dev/shm/PUMP_RUN.* | cut -d'.' -f 2 | tr $'\n' "|" | sed 's#|$#\n#')
    log="${DATE};TERMINATED;${samplesINprocess};${IP};${itype}"
    echo "$log"
    d2=$(($(date +%s)*1000))
    aws logs put-log-events --region $REGION --log-group-name $LOG_GROUP --log-stream-name $LOG_STREAM --log-events "timestamp=${d2},message=${log}"
    shutdown now
    exit 0
done
