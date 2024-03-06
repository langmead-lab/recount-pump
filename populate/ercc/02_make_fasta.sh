#!/bin/bash

fgrep -v ERCC_ID cms_095046.txt | awk -v FS='\t' '{print ">"$1"!"$2"!"$3"!"$4"\n"$5 ; F=sprintf("ercc_%s.fa", $1) ; print ">"$1"!"$2"!"$3"!"$4"\n"$5 > F; close(F) }' > ercc_all.fasta
