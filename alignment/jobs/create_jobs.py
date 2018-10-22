#!/usr/bin/env python

from __future__ import print_function
import os
import sys


limit = 999999
if len(sys.argv) > 1:
    limit = int(sys.argv[1])
    print('Using a limit of %d samples' % limit, file=sys.stderr)

    
HEADER = """#!/bin/bash -l
#SBATCH
#SBATCH --partition=shared
#SBATCH --nodes=1
#SBATCH --mem=%s
#SBATCH --time=20:00:00
#SBATCH --ntasks-per-node=8
"""

with open('../samples.txt', 'rt') as fh:
    samples = fh.read().split()

#TOOLS = ['star', 'hisat2alt1', 'hisat', 'hisat2']
#MEMS = ['36G', '12G', '12G', '12G']
TOOLS = ['hisat2alt1']
MEMS = ['12G']

for tool, mem in zip(TOOLS, MEMS):
    i = 0
    for samp in samples:
        if i >= limit:
            break
        scr_fn = '%s_%s_shared.sh' % (tool, samp)
        if os.path.exists(scr_fn):
            continue
        i += 1
        with open(scr_fn, 'wt') as fh:
            fh.write(HEADER % mem)
            fh.write('#SBATCH --out=.%s_%s.out\n' % (tool, samp))
            fh.write('#SBATCH --err=.%s_%s.err\n' % (tool, samp))
            fh.write('\n')
            fh.write('./run_single_sample_%s_sim.sh %s\n' % (tool, samp))
        print ('sbatch jobs/' + scr_fn)
