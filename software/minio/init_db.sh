#!/bin/bash

# Modeled on https://stackoverflow.com/questions/29145370/how-can-i-initialize-a-mysql-database-with-schema-in-a-docker-container

set -ex

# Start the MySQL daemon in the background.
mysqld --initialize-insecure
mysqld &
mysql_pid=$!

until mysqladmin ping >/dev/null 2>&1; do
  echo -n "."; sleep 0.2
done

# Change root password
mysql -u root --skip-password -e "ALTER USER 'root'@'localhost' IDENTIFIED BY 'recount';"

# Create and empower recount user
mysql -uroot -precount -e "CREATE USER 'recount'@'%' IDENTIFIED BY 'recount';"
mysql -uroot -precount -e "GRANT ALL PRIVILEGES ON * . * TO 'recount'@'%';"

# Print users
mysql -uroot -precount -e "SELECT User, Host FROM mysql.user;"

# Create recount database
mysql -urecount -precount -e "CREATE DATABASE recount;"
mysql -urecount -precount -e "SHOW DATABASES;"

# Tell the MySQL daemon to shutdown.
mysqladmin -uroot -precount shutdown

# Wait for the MySQL daemon to exit.
wait $mysql_pid
