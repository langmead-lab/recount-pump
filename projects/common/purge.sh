#!/bin/sh

ls -l slurm-2*.out | awk '$5 == 488 {print $NF}' | xargs rm -f
