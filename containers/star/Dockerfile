################## BASE IMAGE ######################

FROM biocontainers/biocontainers:latest

################## METADATA ######################
LABEL base.image="biocontainers:latest"
LABEL version="1"
LABEL software="star"
LABEL software.version="2.5.3a"
LABEL website="https://github.com/alexdobin/STAR"
LABEL documentation="https://github.com/alexdobin/STAR/blob/master/doc/STARmanual.pdf"
LABEL license="https://github.com/alexdobin/STAR/blob/master/LICENSE"
LABEL tags="Genomics"

################## MAINTAINER ######################
MAINTAINER Ben Langmead <ben.langmead@gmail.com>

################## INSTALLATION ######################

# https://github.com/alexdobin/STAR/archive/2.5.3a.zip

ENV ZIP=2.5.3a.zip
ENV URL=https://github.com/alexdobin/STAR/archive
ENV FOLDER=STAR-2.5.3a
ENV DST=/home/biodocker/bin
ENV SUBDIR=bin/Linux_x86_64
ENV BINS="STAR STARlong"

RUN wget $URL/$ZIP -O $DST/$ZIP && \
    unzip $DST/$ZIP -d $DST && \
    rm $DST/$ZIP && \
    for bin in $BINS ; do mv $DST/$FOLDER/$SUBDIR/$bin $DST ; done && \
    rm -rf $DST/$FOLDER

WORKDIR /data

CMD ["STAR"]
