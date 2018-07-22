#!/bin/sh

d=`dirname $0`

docker run --rm -d -p 25672:5672 -p 35672:15672  --name rabbitmq `cat $d/image.txt`
