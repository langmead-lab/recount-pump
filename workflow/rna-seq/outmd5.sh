#!/bin/sh

find -s output -type f -exec md5sum {} \; | md5sum | awk '{print $1}'
