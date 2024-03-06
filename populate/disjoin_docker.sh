#!/usr/bin/env bash
image=quay.io/broadsword/recount_pump_populate:1.0.0

d=$(dirname $0)
[[ ! -f disjoin.R ]] && cp $d/disjoin.R .

if [[ $1 == "url" ]] ; then
    shift
    
    url=$1
    shift
    [[ -z "${url}" ]] && echo "Specify URL as 1st argument" && exit 1
    
    name=$1
    shift
    [[ -z "${name}" ]] && echo "Specify name as 2nd argument" && exit 1

    # Run from this directory
    docker run -v `pwd`:/work $image /work/disjoin.R ${url} /work/${name}.bed $*
else
    cp $1 .
    name=$(basename $1)
    shift

    # Run from this directory
    docker run -v `pwd`:/work $image /work/disjoin.R /work/${name} /work/${name}.bed $*
fi
