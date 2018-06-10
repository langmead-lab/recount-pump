#!/bin/sh

docker run --rm -p 3306:3306 -d --name mysql -e MYSQL_ROOT_PASSWORD=password mysql/mysql-server:5.7.22
