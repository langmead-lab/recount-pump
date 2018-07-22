#!/bin/sh

d=`dirname $0`

docker pull $* `cat $d/image.txt`
