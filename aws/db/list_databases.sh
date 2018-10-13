#!/bin/sh

./connect.sh postgres 'SELECT datname FROM pg_database WHERE datistemplate = false;'
