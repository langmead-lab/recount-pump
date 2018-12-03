#!/usr/bin/env python


from __future__ import print_function
import os
import sys
import subprocess
import itertools


def chroms_from_fasta(fn):
    chroms_cmd = "grep '^>' %s | sed 's/^>//' | cut -d' ' -f1" % fn
    out = subprocess.check_output(chroms_cmd, shell=True)
    return out.split()


def chroms_from_gtf(fn):
    chroms_cmd = 'cut -f1 %s | sort -u' % fn
    out = subprocess.check_output(chroms_cmd, shell=True)
    return out.split()


def combo(fa_list, gtf_list):
    fa_set = set(fa_list)
    gtf_set = set(gtf_list)
    fa_not_in_gtf = fa_set.difference(gtf_set)
    gtf_not_in_fa = gtf_set.difference(fa_set)
    print('FA but not GTF: ' + str(fa_not_in_gtf), file=sys.stderr)
    print('GTF but not FA: ' + str(gtf_not_in_fa), file=sys.stderr)


def gtf_and_fasta():
    fasta_sets, gtf_sets = [], []
    for fn in os.listdir('fasta'):
        if not fn.endswith('.fa'):
            continue
        chroms_fa = chroms_from_fasta('fasta/' + fn)
        print("%s chroms: %s" % (fn, str(chroms_fa)), file=sys.stderr)
        fasta_sets.append((fn, chroms_fa))
    for fn in os.listdir('gtf'):
        if not fn.endswith('.gtf'):
            continue
        chroms_gtf = chroms_from_gtf('gtf/' + fn)
        print("%s chroms: %s" % (fn, str(chroms_gtf)), file=sys.stderr)
        gtf_sets.append((fn, chroms_gtf))
    for fa, gtf in itertools.product(fasta_sets, gtf_sets):
        print('\n=== Combo: %s, %s ===\n' % (fa[0], gtf[0]), file=sys.stderr)
        combo(fa[1], gtf[1])
        print('\n=== Combo: %s, %s without alts ===\n' % (fa[0], gtf[0]), file=sys.stderr)
        combo(filter(lambda x: not x.endswith('_alt'), fa[1]), filter(lambda x: not x.endswith('_alt'), gtf[1]))


def isdir(dr):
    return os.path.exists(dr) and os.path.isdir(dr)


def go():
    if isdir('gtf') and isdir('fasta'):
        gtf_and_fasta()


if __name__ == '__main__':
    go()
