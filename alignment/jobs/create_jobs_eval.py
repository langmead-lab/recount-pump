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

# aws --profile jhu-langmead s3 ls s3://recount-reads/human_sim/ | awk '{print $NF}' | sed 's/_sim.*//' | sort -u

samps = ['HG00111_female_GBR_CNAG_CRG_2-1-1',
         'HG00152_male_GBR_LUMC_7-1-1',
         'HG00096_male_GBR_UNIGE_1-1-1',
         'HG00117_male_GBR_LUMC_7-1-1',
         'HG00151_male_GBR_MPIMG_3-1-1',
         'HG00176_female_FIN_ICMB_4-1-1',
         'HG00249_female_GBR_MPIMG_3-1-1',
         'HG00344_female_FIN_ICMB_4-1-1',
         'HG00380_female_FIN_MPIMG_3-1-1',
         'HG01334_male_GBR_LUMC_7-1-1']

modes = ['hg19_annotation_500',
         'hg19_annotation_100',
         'hg19_annotation_50',
         'hg19',
         'hg19_snaptron_500',
         'hg19_snaptron_100',
         'hg19_snaptron_50',
         'hg19_randomdrop_5',
         'hg19_randomdrop_10',
         'hg19_randomdrop_15',
         'hg19_randomdrop_20']

mem = '6G'

for samp, mode in itertools.product(samps, modes):
    if '_female_' in samp:
        mode += '_female'
    else:
        mode += '_male'
    scr_fn = '%s_%s_shared.sh' % (samp, mode)
    if os.path.exists(scr_fn):
        continue
    with open(scr_fn, 'wt') as fh:
        fh.write(HEADER % mem)
        fh.write('#SBATCH --out=.%s_%s.out\n' % (samp, mode))
        fh.write('#SBATCH --err=.%s_%s.err\n' % (samp, mode))
        fh.write('\n')
        fh.write('./eval_sim.sh %s %s\n' % (samp, mode))
    print ('sbatch jobs/' + scr_fn)
