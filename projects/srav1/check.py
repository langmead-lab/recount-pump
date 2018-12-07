#!/usr/bin/env python

from __future__ import print_function
import sys
import re


worker_re = re.compile('worker_([0-9]+)_of_16')
last_time = {}

for ln in sys.stdin:
    toks = ln.split()
    if len(toks) < 6:
        continue
    m = worker_re.match(toks[5])
    if m is not None:
        date = ' '.join(toks[0:3])
        worker = int(m.group(1))
        assert worker <= 16
        last_time[worker] = date

for k, v in sorted(last_time.items()):
    print((k, v))


