q=$1
dlq="${q}_dlq"
echo $dlq

rm -rf queue-messages

key=`fgrep aws_access_key_id ./credentials | head -1 | cut -d'=' -f 2 | sed -e 's/ //g'`
echo $key
secret=`fgrep aws_secret_access_key ./credentials | head -1 | cut -d'=' -f 2 | sed -e 's/ //g'`
echo $secret

#fetch AND delete from queue
/data7/miniconda2/bin/python2 fetch_all_dlq_messages.py -d -q $dlq -r us-east-2 -k $key -s "$secret" > fetch.${dlq}
#/data7/miniconda2/bin/python2 fetch_all_dlq_messages.py -d -q $q -r us-east-2 -k $key -s "$secret" > fetch.${q}

cat queue-messages/* | fgrep "body" | cut -d'"' -f 4 > ${q}.all_strings.txt
#cat queue-messages/* | fgrep "body" | cut -d'"' -f 4 > $dlq.leftovers.txt
#cat queue-messages/* | fgrep "body" | cut -d'"' -f 4 > $q.leftovers.txt

#now re-enqueue
/data7/miniconda2/bin/python2 enqueue_job_messages.py -q $q -f ${q}.all_strings.txt -r us-east-2 -k $key -s "$secret"  2> enqueue.${q}
