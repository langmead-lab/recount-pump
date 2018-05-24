#!/bin/sh

docker exec -it mysql bash -c \
    'mysql -uroot -ppassword -e "CREATE DATABASE recount;" mysql -uroot -ppassword -e "SHOW DATABASES;"'
