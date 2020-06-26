#!/usr/bin/env bash
#meant to be run in the project directory to update the 
#running tranche id to the current one (on the cluster).
#This is for projects that are split into multiple tranches 
#(only human/mouse for recount3)

#e.g. sra_human_v3 or sra_mouse_v1
project=sra_human_v3
ln -fs tranches/tranche_${1}.txt tranche.txt
ln -fs tranches/tranche_${1}.ini tranche.ini
ln -fs tranches/tranche_${1}.ini project.ini
for f in creds/db.ini creds/destination.ini creds/log.ini job-skx-normal_short.sh ; do sed -i -E 's/'$project'_.+$/'$project'_'$1'/' $f ; done
