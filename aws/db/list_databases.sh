#!/bin/sh

./connect.sh 'SELECT datname FROM pg_database WHERE datistemplate = false;'
