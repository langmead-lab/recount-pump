#!/bin/bash

profile=$(grep aws_profile ~/.recount/log.ini | cut -d"=" -f2)
aws logs --profile ${profile} describe-log-groups
