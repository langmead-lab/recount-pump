#!/bin/sh

squeue -l -u $USER | awk '{print $1}' | grep '[0-9]' | xargs scancel
