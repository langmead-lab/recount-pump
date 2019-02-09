#!/bin/bash

awk -v FS='\t' '{print ">"$1"!"$2"!"$3"!"$4"\n"$5 ; F=sprintf("ercc_%s.fa", $1) ; print ">"$1"!"$2"!"$3"!"$4"\n"$5 > F; close(F) }' cms_095047.txt > ercc_all.fasta
