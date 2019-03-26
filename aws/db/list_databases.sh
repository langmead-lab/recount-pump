#!/usr/bin/env bash

d=$(dirname $0)

$d/connect.sh postgres 'SELECT datname FROM pg_database WHERE datistemplate = false;'
