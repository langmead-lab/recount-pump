#!/bin/sh

docker build $* -t `cat image.txt` .
