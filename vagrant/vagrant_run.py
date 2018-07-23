#!/usr/bin/env python

# Author: Ben Langmead <ben.langmead@gmail.com>
# License: MIT

"""vagrant_run

Usage:
  vagrant_run [options]

Options:
  --skip-run                 Skip running Vagrant, just look at vagrant.log.
  --slack-ini <ini>          ini file for Slack webhooks [default: ~/.recount/slack.ini].
  --slack-section <section>  ini file section for log aggregator [default: slack].
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


def run(skip_run, ini_fn, section):
    slack_url = slack_webhook_url(ini_fn, section=section)
    if not skip_run:
        os.system('vagrant up 2>&1 | tee vagrant.log')
    attachments = []
    with open('vagrant.log', 'rb') as fh:
        for ln in fh:
            if '===HAPPY' in ln:
                st = ln[ln.find(b'===HAPPY')+9:].rstrip()
                attachments.append({'text': st, 'color': 'good'})
            elif '===SAD' in ln:
                st = ln[ln.find(b'===SAD')+7:].rstrip()
                attachments.append({'text': st, 'color': 'danger'})
    requests.put(slack_url, json={
        'username': 'webhookbot',
        'text': 'recount-pump build-deploy-test suite:',
        'attachments': attachments})
    if not skip_run:
        os.system('vagrant destroy -f')


if __name__ == '__main__':
    args = docopt(__doc__)
    slack_ini = os.path.expanduser(args['--slack-ini'])
    run(args['--skip-run'], slack_ini, args['--slack-section'])
