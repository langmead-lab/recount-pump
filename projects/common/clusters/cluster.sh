#!/usr/bin/env bash

if [[ -f /etc/motd ]] && grep -q Stampede2 /etc/motd ; then
    echo stampede2
elif echo $(hostname) | grep -q bc-login ; then
    echo marcc
elif [[ -f /etc/hosts ]] && grep -q hhpc /etc/hosts ; then
    echo hhpc
else
    echo "Unknown cluster"
    exit 1
fi
