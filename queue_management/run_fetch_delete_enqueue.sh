q=$1
dlq="${q}_dlq"
echo $dlq

key=`fgrep aws_access_key_id ./credentials | head -1 | cut -d'=' -f 2 | sed -e 's/ //g'`
echo $key
secret=`fgrep aws_secret_access_key ./credentials | head -1 | cut -d'=' -f 2 | sed -e 's/ //g'`
echo $secret

#fetch AND delete from queue
python2 fetch_all_dlq_messages.py -d -q $dlq -r us-east-2 -k $key -s $secret > fetch.${dlq}

cat queue-messages/* | fgrep "body" | cut -d'"' -f 4 > ${q}.all_strings.txt

#now re-enqueue
python2 enqueue_job_messages.py -q $q -f ${q}.all_strings.txt -r us-east-2 -k $key -s $secret  2> enqueue.${q}
