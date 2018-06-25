#!/bin/sh

docker-compose build && docker-compose up --abort-on-container-exit
