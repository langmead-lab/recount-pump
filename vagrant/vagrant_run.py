#!/usr/bin/env python

# Author: Ben Langmead <ben.langmead@gmail.com>
# License: MIT

"""vagrant_run

Usage:
  vagrant_run run [options]
  vagrant_run ssh [options]
  vagrant_run destroy [options]

Options:
  --aws-json <path>          Path to file defining AWS-related variables [default: ../aws.json].
  --aws-profile <path>       Path to file defining AWS-related variables [default: jhu_ue2].
  --skip-slack               Don't send message to Slack.
  --no-destroy-on-error      Keep instance running on error.
  --slack-ini <ini>          ini file for Slack webhooks [default: ~/.recount/slack.ini].
  --slack-section <section>  ini file load_aws_json()section for log aggregator [default: slack].
  -a, --aggregate            Enable log aggregation.
  -h, --help                 Show this screen.
  --version                  Show version.
"""

""" ~/.recount/slack.ini file should look like this:
[slack]
tstring=TXXXXXXXX
bstring=BXXXXXXXX
secret=XXXXXXXXXXXXXXXXXXXXXXXX
"""

import os
import sys
import requests
import json
from docopt import docopt
try:
    from configparser import RawConfigParser
except ImportError:
    from ConfigParser import RawConfigParser
    sys.exc_clear()


def slack_webhook_url(ini_fn, section='slack'):
    tstring, bstring, secret = read_slack_config(ini_fn, section=section)
    return 'https://hooks.slack.com/services/%s/%s/%s' % (tstring, bstring, secret)


def read_slack_config(ini_fn, section='slack'):
    cfg = RawConfigParser()
    cfg.read(ini_fn)
    if section not in cfg.sections():
        raise RuntimeError('No [%s] section in log ini file "%s"' % (section, ini_fn))
    tstring, bstring, secret = cfg.get(section, 'tstring'), cfg.get(section, 'bstring'), cfg.get(section, 'secret')
    return tstring, bstring, secret


def load_aws_json(json_fn, profile):
    js = json.loads(open(json_fn, 'rt').read())
    if profile not in js['profile']:
        raise RuntimeError('No such profile as "%s" in AWS config "%s"' % (profile, json_fn))
    js_prof = js['profile'][profile]
    region = js_prof['region']
    subnet = js_prof['subnet'][js_prof['subnet'].keys()[0]]
    security_group = js_prof['security_group']
    ami = js['ec2']['ami'][region]
    keypair = js_prof['keypair']
    bid_price = js['ec2']['bid_price'][region]
    instance_type = js['ec2']['instance_type']
    aws_profile = js_prof['profile']
    return region, subnet, security_group, ami, keypair, bid_price, instance_type, aws_profile


def run(command, skip_slack, ini_fn, section, aws_json, profile, no_destroy):
    if not os.path.exists(aws_json):
        raise RuntimeError('AWS json file "%s" does not exist' % aws_json)
    region, subnet, security_group, ami, keypair, bid_price, instance_type, aws_profile = load_aws_json(aws_json, profile)
    os.environ['VAGRANT_AWS_PROFILE'] = aws_profile
    os.environ['VAGRANT_AWS_REGION'] = region
    os.environ['VAGRANT_AWS_SUBNET_ID'] = subnet
    os.environ['VAGRANT_AWS_SECURITY_GROUP'] = security_group
    os.environ['VAGRANT_AWS_AMI'] = ami
    os.environ['VAGRANT_AWS_EC2_KEYPAIR'] = keypair
    os.environ['VAGRANT_AWS_EC2_INSTANCE_TYPE'] = instance_type
    os.environ['VAGRANT_AWS_EC2_BID_PRICE'] = bid_price
    slack_url = slack_webhook_url(ini_fn, section=section)
    vagrant_args = ''
    if no_destroy:
        vagrant_args += ' --no-destroy-on-error'
    if command == 'run':
        os.system('vagrant up %s 2>&1 | tee vagrant.log' % vagrant_args)
        attachments = []
        with open('vagrant.log', 'r') as fh:
            for ln in fh:
                if '===HAPPY' in ln:
                    st = ln[ln.find('===HAPPY') + 9:].rstrip()
                    attachments.append({'text': st, 'color': 'good'})
                elif '===SAD' in ln:
                    st = ln[ln.find('===SAD') + 7:].rstrip()
                    attachments.append({'text': st, 'color': 'danger'})
        if not skip_slack:
            name = 'no name'
            if os.path.exists('name.txt'):
                with open('name.txt', 'rt') as fh:
                    name = fh.read().strip()
            requests.put(slack_url, json={
                'username': 'webhookbot',
                'text': '%s:' % name,
                'attachments': attachments})
        if not skip_run:
            os.system('vagrant destroy -f')
    elif command == 'ssh':
        os.system('vagrant ssh')
    elif command == 'destroy':
        os.system('vagrant destroy')
    else:
        raise ValueError('Unexpected command: "%s"' % command)


if __name__ == '__main__':
    args = docopt(__doc__)
    slack_ini = os.path.expanduser(args['--slack-ini'])
    if args['run']:
        run('run', args['--skip-slack'], slack_ini,
            args['--slack-section'], args['--aws-json'], args['--aws-profile'],
            args['--no-destroy-on-error'])
    elif args['ssh']:
        run('ssh', args['--skip-slack'], slack_ini,
            args['--slack-section'], args['--aws-json'], args['--aws-profile'],
            args['--no-destroy-on-error'])
    elif args['destroy']:
        run('ssh', args['--skip-slack'], slack_ini,
            args['--slack-section'], args['--aws-json'], args['--aws-profile'],
            args['--no-destroy-on-error'])
    else:
        raise ValueError('No such command')

