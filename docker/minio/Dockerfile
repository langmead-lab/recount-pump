FROM minio/minio:RELEASE.2019-03-27T22-35-21Z

# From parent Dockerfile:

# ENTRYPOINT ["/usr/bin/docker-entrypoint.sh"]
# VOLUME ["/data"]
# CMD ["minio"]

# Entrypoint script:

# https://github.com/minio/minio/blob/master/dockerscripts/docker-entrypoint.sh
# - prepends "minio" onto command
# - manages docker secrets

RUN curl -L -o mc https://dl.minio.io/client/mc/release/linux-amd64/mc
RUN chmod a+x mc
RUN mv mc /usr/local/bin

RUN apk update
RUN apk add -u bash
RUN apk add -u mc
RUN apk add -u tree
RUN apk add -u gcc
RUN apk add -u g++
RUN apk add -u python
RUN apk add -u python-dev
RUN python -m ensurepip
RUN pip install --upgrade pip
RUN apk add -u musl-dev postgresql-dev postgresql postgresql-libs
RUN apk add -u linux-headers
RUN ln -s /usr/include/locale.h /usr/include/xlocale.h

COPY requirements.txt /tmp/requirements.txt
RUN pip install --quiet -r /tmp/requirements.txt

COPY credentials /tmp/credentials
COPY manifest.csv /tmp/manifest.csv
COPY wait-for-it.sh /tmp/wait-for-it.sh
COPY init_db.sh /tmp/init_db.sh
COPY start_db.sh /tmp/start_db.sh
COPY src /tmp/src

RUN . /tmp/init_db.sh
ENTRYPOINT /tmp/start_db.sh
