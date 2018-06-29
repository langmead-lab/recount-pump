FROM minio/minio

# From parent Dockerfile:

# ENTRYPOINT ["/usr/bin/docker-entrypoint.sh"]
# VOLUME ["/data"]
# CMD ["minio"]

# Entrypoint script:

# https://github.com/minio/minio/blob/master/dockerscripts/docker-entrypoint.sh
# - prepends "minio" onto command
# - manages docker secrets

RUN apk update
RUN apk add -u bash
RUN apk add -u mc
RUN apk add tree
RUN wget https://dl.minio.io/client/mc/release/linux-amd64/mc
RUN chmod a+x mc
RUN mv mc /usr/local/bin

COPY credentials /tmp/credentials
COPY manifest.csv /tmp/manifest.csv
COPY wait-for-it.sh /tmp/wait-for-it.sh
COPY init_db.sh /tmp/init_db.sh
COPY start_db.sh /tmp/start_db.sh

RUN . /tmp/init_db.sh
ENTRYPOINT /tmp/start_db.sh
