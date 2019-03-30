FROM python:3.4-stretch
WORKDIR /code

RUN printf "deb http://httpredir.debian.org/debian stretch-backports main non-free\ndeb-src http://httpredir.debian.org/debian stretch-backports main non-free" > /etc/apt/sources.list.d/backports.list

RUN apt-get update -y && apt-get install -y apt-transport-https dirmngr
RUN echo 'deb https://apt.dockerproject.org/repo debian-stretch main' >> /etc/apt/sources.list
#RUN apt-key adv --keyserver hkp://p80.pool.sks-keyservers.net:80 --recv-keys F76221572C52609D
RUN apt-get update -y && \
    apt-get install -y --allow-unauthenticated docker-engine
RUN apt-get update -y && \
    apt-get install -y libarchive-dev squashfs-tools graphviz && \
    apt-get -t stretch-backports install singularity-container

RUN pip install --upgrade pip

ADD requirements.txt /code
RUN pip install --quiet -r requirements.txt

RUN curl -L -o mc https://dl.minio.io/client/mc/release/linux-amd64/mc
RUN chmod a+x mc
RUN mv mc /usr/local/bin

RUN mkdir -p /root/.recount /root/.aws

ADD wait-for-it.sh /code
ADD unit_test.sh /code
ADD e2e_test.sh /code
ADD test_entry.sh /code
ADD src /code/src

RUN wget https://raw.githubusercontent.com/singularityware/docker2singularity/master/docker2singularity.sh
RUN mv docker2singularity.sh /usr/local/bin
RUN chmod a+x /usr/local/bin/docker2singularity.sh
