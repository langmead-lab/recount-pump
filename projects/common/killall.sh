#!/bin/sh

# Kills all analysis jobs (actually, all the user's jobs!) currently underway,
# assuming Slurm

# TODO: just kill recount-related jobs

squeue -l -u ${USER} | awk '{print $1}' | grep '[0-9]' | xargs scancel
