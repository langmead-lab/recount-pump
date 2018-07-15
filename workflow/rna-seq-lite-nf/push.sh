#!/bin/sh

docker push $* `cat image.txt`
