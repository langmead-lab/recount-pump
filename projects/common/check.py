#!/usr/bin/env python

from __future__ import print_function
import sys
import re
import os
from datetime import datetime


worker_re = re.compile('worker_([0-9]+)_of_16')

for fn in os.listdir('.'):
    if not (fn.startswith('slurm-') and fn.endswith('.out')):
        continue
    print(fn)
    last_time = {}
    with open(fn, 'rt') as fh:
        for ln in fh:
            ln = ln.rstrip()
            toks = ln.split()
            if len(toks) < 6:
                continue
            m = worker_re.match(toks[5])
            if m is not None:
                date = ' '.join(toks[0:3])
                worker = int(m.group(1))
                assert worker <= 16
                last_time[worker] = (date, ln)

    if len(last_time) == 0:
        continue

    times = []
    for k, v in sorted(last_time.items()):
        dt, ln = v
        tm = datetime.strptime(dt, '%b %d %H:%M:%S')
        times.append(int(tm.strftime("%s")))

    med_time = list(sorted(times))[len(times)//2]
    print('Median time: %d' % med_time)

    print('Long timings:')

    for k, v in sorted(last_time.items()): 
        dt, ln = v
        tm = datetime.strptime(dt, '%b %d %H:%M:%S')
        secs = int(tm.strftime("%s"))
        if med_time - secs > 60 * 60 * 3:
            print((k, dt))
            print(ln)

