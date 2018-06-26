#!/bin/sh

docker run --rm -d -p 5672:5672 -p 15672:15672  --name rabbitmq rabbitmq
