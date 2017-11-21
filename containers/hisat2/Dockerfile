################## BASE IMAGE ######################

FROM biocontainers/biocontainers:latest

################## METADATA ######################
LABEL base.image="biocontainers:latest"
LABEL version="1"
LABEL software="hisat2"
LABEL software.version="2.1.0"
LABEL website="http://bowtie-bio.sourceforge.net/bowtie2/index.shtml"
LABEL documentation="http://bowtie-bio.sourceforge.net/bowtie2/index.shtml"
LABEL license="http://bowtie-bio.sourceforge.net/bowtie2/index.shtml"
LABEL tags="Genomics"

################## MAINTAINER ######################
MAINTAINER Ben Langmead <ben.langmead@gmail.com>

################## INSTALLATION ######################

ENV ZIP=hisat2-2.1.0-Linux_x86_64.zip
ENV URL=ftp://ftp.ccb.jhu.edu/pub/infphilo/hisat2/downloads
ENV FOLDER=hisat2-2.1.0
ENV DST=/home/biodocker/bin

RUN wget $URL/$ZIP -O $DST/$ZIP && \
    unzip $DST/$ZIP -d $DST && \
    rm $DST/$ZIP && \
    mv $DST/$FOLDER/* $DST && \
    rmdir $DST/$FOLDER

WORKDIR /data

CMD ["hisat2"]
