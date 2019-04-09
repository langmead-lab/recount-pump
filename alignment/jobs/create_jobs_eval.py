#!/usr/bin/env python

from __future__ import print_function
import os
import sys
import itertools


HEADER = """#!/bin/bash -l
#SBATCH
#SBATCH --partition=shared
#SBATCH --nodes=1
#SBATCH --mem=%s
#SBATCH --time=4:00:00
#SBATCH --ntasks-per-node=8
"""

samps = ['HG00111_female_GBR_CNAG_CRG_2-1-1', 'HG00152_male_GBR_LUMC_7-1-1']
modes = ['humansim_annotation_500oh',
         'humansim_annotation_50oh',
         'humansim_annotation',
         'humansim_hg38',
         'humansim_recount2_500oh',
         'humansim_recount2_50oh',
         'humansim_recount2']
mem = '4G'

for samp, mode in itertools.product(samps, modes):
    scr_fn = '%s_%s_shared.sh' % (samp, mode)
    if os.path.exists(scr_fn):
        continue
    with open(scr_fn, 'wt') as fh:
        fh.write(HEADER % mem)
        fh.write('#SBATCH --out=.%s_%s.out\n' % (samp, mode))
        fh.write('#SBATCH --err=.%s_%s.err\n' % (samp, mode))
        fh.write('\n')
        fh.write('./eval_sim.sh %s %s' % (samp, mode))
    print ('sbatch jobs/' + scr_fn)
