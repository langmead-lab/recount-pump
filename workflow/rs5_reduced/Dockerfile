FROM ubuntu:20.04

USER root

ENV DEBIAN_FRONTEND=noninteractive
#RUN apt update -yy
#RUN apt-get update -y && apt-get install software-properties-common cmake curl libncurses5-dev unzip wget git gcc g++ make zip -y
RUN apt-get update -y && apt-get install cmake curl wget git gcc g++ make -y
RUN apt install parallel libbz2-dev liblzma-dev zlib1g-dev libcurl4-openssl-dev -yy
RUN apt install python3 python3-pip rsync -yy

RUN mkdir /monorail_bin
ENV PATH="/monorail_bin:$PATH"
RUN mkdir /temp
WORKDIR /temp

RUN apt install -yy snakemake=5.10.0-2

# install samtools
RUN apt-get install -y autoconf gcc make
ENV SM_VER=1.9
RUN curl -OL https://github.com/samtools/samtools/releases/download/${SM_VER}/samtools-${SM_VER}.tar.bz2 && \
    bzip2 -dc samtools-${SM_VER}.tar.bz2 | tar xvf - && \
    rm -f samtools-${SM_VER}.tar.bz2 && \
    cd samtools-${SM_VER} && \
    autoheader && \
    autoconf && \
    ./configure --disable-bz2 --disable-lzma --disable-libcurl --without-libdeflate --without-curses && \
    make && \
    make install

#sratoolkit
#from https://github.com/ncbi/sra-tools/issues/489
RUN git clone https://github.com/ncbi/ncbi-vdb.git
RUN cd ncbi-vdb && ./configure && make
RUN git clone https://github.com/ncbi/sra-tools.git
RUN cd sra-tools && ./configure && make
RUN rsync -av ~/ncbi-outdir/sra-tools/linux/gcc/arm64/rel/bin/* /monorail_bin/

#parallel-fastq-dump
RUN wget https://github.com/rvalieris/parallel-fastq-dump/archive/refs/tags/0.6.6.tar.gz
RUN tar -zxvf 0.6.6.tar.gz
RUN rsync -av parallel-fastq-dump-0.6.6/parallel-fastq-dump /monorail_bin/
#RUN python3 ~/bin/parallel-fastq-dump

#STAR
#rna-star/focal 2.7.3a+dfsg-1build2
RUN apt install -yy rna-star=2.7.3a+dfsg-1build2

#regtools
RUN wget https://github.com/griffithlab/regtools/archive/refs/tags/0.5.0.tar.gz
RUN tar -zxvf 0.5.0.tar.gz
RUN cd regtools-0.5.0 && cmake ./ && make
RUN rsync -av regtools-0.5.0/regtools /monorail_bin/

#seqtk
RUN wget https://github.com/lh3/seqtk/archive/refs/tags/v1.3.tar.gz
RUN tar -zxvf v1.3.tar.gz
RUN cd seqtk-1.3 && make && rsync -av seqtk /monorail_bin/

#zstd
#ZVER=1.4.2 
#faster than 1.3.3
ENV ZVER=1.3.3
RUN wget https://github.com/facebook/zstd/archive/refs/tags/v${ZVER}.tar.gz
RUN tar -zxvf v${ZVER}.tar.gz
RUN cd zstd-${ZVER} && make && rsync -av zstd /monorail_bin/

#subread
#change -mtune=core2 to -mcpu=native in all Makefiles before compilation as per:
#https://community.arm.com/arm-community-blogs/b/tools-software-ides-blog/posts/compiler-flags-across-architectures-march-mtune-and-mcp
RUN wget https://sourceforge.net/projects/subread/files/subread-1.6.3/subread-1.6.3-source.tar.gz/download -O subread-1.6.3-source.tar.gz
RUN tar -zxvf subread-1.6.3-source.tar.gz
WORKDIR /temp/subread-1.6.3-source/src
RUN sed -i 's#-mtune=core2#-mcpu=native#g' Makefile.Linux
RUN sed -i 's#-mtune=core2#-mcpu=native#g' ./longread-one/Makefile
RUN make -f Makefile.Linux
RUN rsync -av ../bin/featureCounts /monorail_bin/
WORKDIR /temp


RUN wget https://github.com/ChristopherWilks/megadepth/releases/download/0.4.0/bamcount.aarch64
RUN rsync -av bamcount.aarch64 /monorail_bin/bamcount
RUN mkdir /bamcount
RUN rsync -av bamcount.aarch64 /bamcount/bamcount
RUN chmod a+x /monorail_bin/bamcount
RUN chmod a+x /bamcount/bamcount

WORKDIR /
RUN rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*
RUN apt-get clean
RUN apt-get autoremove -y
RUN rm -rf /var/lib/{apt,dpkg,cache,log}/ /temp

#UPDATE don't install salmon
#salmon 0.12.0
##boost (needed for salmon 0.12.0)
#apt update && sudo apt upgrade
#apt-get install build-essential g++ python3-dev autotools-dev libicu-dev libbz2-dev libboost-all-dev liblzma-dev
#wget https://boostorg.jfrog.io/artifactory/main/release/1.63.0/source/boost_1_63_0.tar.gz
#tar -zxvf boost_1_63_0.tar.gz
#pushd boost_1_63_0
#./bootstrap.sh --prefix=/usr/
#./b2
#popd
#export BOOST_INCLUDEDIR=/home/ubuntu/boost_1_63_0
#export BOOST_LIBRARYDIR=/home/ubuntu/boost_1_63_0/stage/lib
#wget https://github.com/COMBINE-lab/salmon/releases/download/v0.12.0/salmon-0.12.0_linux_x86_64.tar.gz
#cmake ./
#need to fix tbb sha256 sum from 23793c8645480148e9559df96b386b780f92194c80120acce79fcdaae0d81f45 to e5f19d747f6adabfc7daf2cc0a1ddcfab0f26bc083d70ea0a63def4a9f3919c5
#make

# install Snakefile
COPY Snakefile /Snakefile
RUN chmod a+r /Snakefile

# install generic workflow wrapper script
COPY workflow.bash /workflow.bash
RUN chmod a+rx /workflow.bash

# install download.sh
COPY download.sh /download.sh
RUN chmod a+r /download.sh

RUN useradd -ms /bin/bash recount && chpasswd recount:recount
USER recount
WORKDIR /home/recount/

# See src/run.py where this command is repeated
#CMD ["bash", "-c", "source activate recount && /workflow.bash"]
CMD ["bash", "-c", "/workflow.bash"]
