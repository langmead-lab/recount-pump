#!/bin/bash

d=$(dirname $0)
image=$(cat $d/image.txt)

docker pull $* ${image}
