#!/bin/sh

docker exec -it mysql bash -c \
    'mysql -uroot -ppassword -e "CREATE USER '"'"'recount'"'"'@'"'"'%'"'"' IDENTIFIED BY '"'"'password'"'"'; GRANT ALL PRIVILEGES ON * . * TO '"'"'recount'"'"'@'"'"'%'"'"';"'

sh list_users.sh
