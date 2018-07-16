#!/bin/sh

find output -type f -exec md5sum {} \; | sort | md5sum | awk '{print $1}'
