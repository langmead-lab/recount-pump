#!/usr/bin/env python


from __future__ import print_function
import os
import sys
import subprocess


def chroms_from_fasta(fn):
    chroms_cmd = "grep '^>' %s | sed 's/^>//' | cut -d' ' -f1" % fn
    out = subprocess.check_output(chroms_cmd, shell=True)
    return out.split()


def chroms_from_gtf(fn):
    chroms_cmd = 'cut -f1 %s | sort -u' % fn
    out = subprocess.check_output(chroms_cmd, shell=True)
    return out.split()


def gtf_and_fasta():
    for fn in os.listdir('fasta'):
        if not fn.endswith('.fa'):
            continue
        chroms_fa = chroms_from_fasta('fasta/' + fn)
        print("%s chroms: %s" % (fn, str(chroms_fa)), file=sys.stderr)
    for fn in os.listdir('gtf'):
        if not fn.endswith('.gtf'):
            continue
        chroms_gtf = chroms_from_gtf('gtf/' + fn)
        print("%s chroms: %s" % (fn, str(chroms_gtf)), file=sys.stderr)


def isdir(dr):
    return os.path.exists(dr) and os.path.isdir(dr)


def go():
    if isdir('gtf') and isdir('fasta'):
        gtf_and_fasta()


if __name__ == '__main__':
    go()
