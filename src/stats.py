#!/usr/bin/env python

# Author: Ben Langmead <ben.langmead@gmail.com>
# License: MIT

"""stats.py

Usage:
  stats summarize <stats-file> [options]

Options:
  --prefix <path>          Write plot files beginning with <path> [default: recount].
  --db-ini <ini>           Database ini file [default: ~/.recount/db.ini].
  --db-section <section>   ini file section for database [default: client].
  --log-ini <ini>          ini file for log aggregator [default: ~/.recount/log.ini].
  --log-level <level>      set level for log aggregation; could be CRITICAL,
                           ERROR, WARNING, INFO, DEBUG [default: INFO].
  --ini-base <path>        Modify default base path for ini files.
  -h, --help               Show this screen.
  --version                Show version.
"""

import os
import re
import json
import tempfile


def to_camel_case(st):
    """
    Based on: https://dev.to/rrampage/snake-case-to-camel-case-and-back-using-regular-expressions-and-python-m9j
    """
    assert st is not None
    if len(st) == 0:
        return st

    snake_re = r"(.*?)_([a-zA-Z])"

    def camel_upper(match):
        return match.group(1)[0].upper() + match.group(1)[1:] + match.group(2).upper()

    return re.sub(snake_re, camel_upper, st[0].upper() + st[1:], 0)


def summarize(fn):
    outer_keys = ['total_runtime', 'rules', 'files']
    counters = []
    assert os.path.exists(fn)
    with open(fn, 'rt') as fh:
        js = json.loads(fh.read())
    for okey in outer_keys:
        assert okey in js  # dokey
    fkeys = set()
    for fkey, _ in js['files'].items():
        fkey = fkey.split('/')[-1]
        fkey = re.split('[_\.]', fkey)[:3]
        fkeys.add('_'.join(fkey))
    ninputs = len(fkeys)

    for rkey, rval in js['rules'].items():
        assert 'mean-runtime' in rval
        mr = float(rval['mean-runtime'])
        counters.append((to_camel_case(rkey), mr * ninputs))

    return counters


def test_to_camel_1():
    assert 'Happy' == to_camel_case('Happy')
    assert 'Happy' == to_camel_case('happy')


def test_to_camel_2():
    assert 'HelloWorld' == to_camel_case('hello_world')


def test_summarize_1():
    tmpdir = tempfile.mkdtemp()
    tmpfn = os.path.join(tmpdir, 'test.json')
    js = {'total_runtime': {},
          'files': {'ERR204964_ERP001942_hg38_0.fastq': 7},
          'rules': {'my_rule': {'mean-runtime': 70.7},
                    'otherrule': {'mean-runtime': 80.8}}}
    with open(tmpfn, 'wt') as fh:
        fh.write(json.dumps(js, sort_keys=True) + '\n')
    counters = summarize(tmpfn)
    assert 2 == len(counters)
    assert 'MyRule' == counters[0][0]
    assert 70.7 == counters[0][1]
    assert 'Otherrule' == counters[1][0]
    assert 80.8 == counters[1][1]


def go():
    pass


if __name__ == '__main__':
    go()
