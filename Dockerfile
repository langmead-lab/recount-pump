FROM python:3.4-jessie
WORKDIR /code

RUN apt-get update
RUN apt-get install -y emacs-nox

RUN wget -q https://github.com/singularityware/singularity/releases/download/2.3.1/singularity-2.3.1.tar.gz
RUN tar xf singularity-2.3.1.tar.gz
RUN cd singularity-2.3.1 && \
        ./configure --prefix=/usr/local >/dev/null && \
        make >/dev/null && \
        make install >/dev/null && \
        cd .. && \
        rm -rf singularity-2.3.1

ADD wait-for-it.sh /code
ADD requirements.txt /code
RUN pip install --quiet -r requirements.txt

ADD src /code/src
