#!/usr/bin/env bash

if [[ -f /etc/motd ]] && grep -q Stampede2 /etc/motd ; then
    echo stampede2
elif [[ -f /etc/motd ]] && grep -q 'bridges\.psc\.edu' /etc/motd ; then
    echo bridges
elif echo $(hostname) | grep -q bc-login ; then
    echo marcc
elif [[ -f /etc/hosts ]] && grep -q hhpc /etc/hosts ; then
    echo hhpc
else
    echo "Unknown cluster"
    exit 1
fi
