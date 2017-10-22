#!/bin/sh

VER=1.2
VERDASH=1-2

FN=metasra.v${VERDASH}.sqlite
URL=http://metasra.biostat.wisc.edu/static/metasra_versions/v${VER}/${FN}

if [ ! -f ${FN} ] ; then
    wget -O ${FN} ${URL}
fi
