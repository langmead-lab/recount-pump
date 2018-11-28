FROM continuumio/miniconda:4.5.11

#ADD http://download.asperasoft.com/download/sw/ascp-client/3.5.4/ascp-install-3.5.4.102989-linux-64.sh /tmp/

#RUN test $(sha1sum /tmp/ascp-install-3.5.4.102989-linux-64.sh |cut -f1 -d\ ) = a99a63a85fee418d16000a1a51cc70b489755957 && \
#    sh /tmp/ascp-install-3.5.4.102989-linux-64.sh

RUN curl -LO https://download.asperasoft.com/download/sw/connect/3.7.4/aspera-connect-3.7.4.147727-linux-64.tar.gz && \
    tar zxf aspera-connect-3.7.4.147727-linux-64.tar.gz && \
    rm -f aspera-connect-3.7.4.147727-linux-64.tar.gz

RUN conda install -c bioconda sra-tools

RUN apt-get update -y && apt-get install -y procps

RUN echo '/aspera-connect-3.7.4.147727-linux-64.sh' >> /etc/skel/.bashrc

RUN useradd -ms /bin/bash recount && chpasswd recount:recount

USER recount
WORKDIR /home/recount
