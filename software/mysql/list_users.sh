#!/bin/sh

docker exec -it mysql bash -c \
    'mysql -uroot -ppassword -e "SELECT User, Host FROM mysql.user;"'
