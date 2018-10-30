#!/usr/bin/env python

# Author: Ben Langmead <ben.langmead@gmail.com>
# License: MIT

"""
Convert GTF to a CSV suitable for loading into a data frame.  Each attribute
gets a column.  For records lacking an attribute, value is NA.
"""

from __future__ import print_function
import sys


def parse_gtf_cols(fn, limit=5000):
    cols = ['chromosome', 'annotation', 'type', 'start', 'end', 'score', 'strand', 'frame']
    attr_dict = {}
    with open(fn, 'rt') as fh:
        streak = 0
        for ln in fh:
            if ln[0] == '#':
                continue
            len_before = len(attr_dict)
            ln = ln.rstrip()
            toks = ln.split('\t')
            attributes = toks[-1]
            for atok in attributes.split(';'):
                atok = atok.strip()
                if len(atok) == 0:
                    continue
                kv = atok.split()
                assert 2 == len(kv), kv
                attr_dict[kv[0]] = kv[1]
            if len_before == len(attr_dict):
                streak += 1
                if streak > limit:
                    break
            else:
                streak = 0
    print(attr_dict, file=sys.stderr)
    attr_dict_keys = list(sorted(attr_dict.keys()))
    cols += attr_dict_keys
    print(','.join(cols))
    with open(fn, 'rt') as fh:
        for ln in fh:
            if ln[0] == '#':
                continue
            ln = ln.rstrip()
            toks = ln.split('\t')
            attributes = toks[-1]
            toks = toks[:-1]
            attr_dict_rec = {}
            for atok in attributes.split(';'):
                atok = atok.strip()
                if len(atok) == 0:
                    continue
                kv = atok.split()
                assert kv[0] in attr_dict
                assert 2 == len(kv), kv
                attr_dict_rec[kv[0]] = kv[1]
            for key in attr_dict_keys:
                if key in attr_dict_rec:
                    toks.append(attr_dict_rec[key])
                else:
                    toks.append('NA')
            print(','.join(toks))


def go():
    parse_gtf_cols(sys.argv[1])


if __name__ == '__main__':
    go()
