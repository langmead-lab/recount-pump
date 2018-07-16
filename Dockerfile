FROM python:3.4-jessie
WORKDIR /code

RUN apt-get update
RUN apt-get install -y emacs-nox

RUN wget https://github.com/singularityware/singularity/releases/download/2.3.1/singularity-2.3.1.tar.gz
RUN tar xvf singularity-2.3.1.tar.gz
RUN cd singularity-2.3.1 && ./configure --prefix=/usr/local && make && make install && cd .. && rm -rf singularity-2.3.1

ADD wait-for-it.sh /code
ADD requirements.txt /code
RUN pip install --quiet -r requirements.txt

ADD src /code/src
