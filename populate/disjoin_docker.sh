#!/usr/bin/env bash

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
    docker run -it \
        -v `pwd`:/work bioconductor/release_core2 \
        /work/disjoin.R ${url} /work/${name}.bed $*
else
    cp $1 .
    name=$(basename $1)
    shift

    # Run from this directory
    docker run -it \
        -v `pwd`:/work bioconductor/release_core2 \
        /work/disjoin.R /work/${name} /work/${name}.bed $*
fi
