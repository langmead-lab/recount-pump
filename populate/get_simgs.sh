#!/bin/sh

IMAGES="hisat2 star"

[ -n "${SINGULARITY_CACHEDIR}" ] && echo "Set SINGULARITY_CACHEDIR to destination dir" && exit 1

for nm in $IMAGES ; do
    singularity pull --name "${SINGULARITY_CACHEDIR}/${nm}" shub://langmead-lab/recount-pump:${nm}
done
