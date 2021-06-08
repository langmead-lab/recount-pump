#!/usr/bin/env bash

set -ex

if [[ ! -f samples.tsv.gz && ! -f samples.tsv ]] ; then
	wget http://snaptron.cs.jhu.edu/data/srav3h/samples.tsv.gz
fi

if [[ ! -f samples.sorted_by_study.tsv.gz && ! -f samples.sorted_by_study.tsv ]] ; then
	wget http://snaptron.cs.jhu.edu/data/srav3h/samples.sorted_by_study.tsv.gz
fi

if [[ ! -f samples.fields.tsv ]] ; then
	wget http://snaptron.cs.jhu.edu/data/srav3h/samples.fields.tsv
fi

if [[ ! -f genes.bgz ]] ; then
	wget http://snaptron.cs.jhu.edu/data/srav3h/genes.bgz
fi
