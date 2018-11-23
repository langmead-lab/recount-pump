#!/usr/bin/env python

# Author: Ben Langmead <ben.langmead@gmail.com>
# License: MIT

"""attempt_match

Usage:
  attempt_match sweep <dir>
  attempt_match compare <dir1> <dir2>

Options:
  -h, --help               Show this screen.
  --version                Show version.
"""


from __future__ import print_function
from docopt import docopt
from toolbox import md5
from collections import defaultdict
import os
import re
import sys
import tempfile


"""
Traverse a directory structure containing attempts from a recount-pump
workflow.  For the files that should not differ from attempt to attempt, check
whether the attempts do indeed have matching files.  Output a concise summary.
Optionally prune away redundant attempts after matching. 
"""


def shorten(fn):
    return '.'.join(fn.split('.')[1:])


def compare(dir1, dir2, ignores=None):
    """
    Compare the output files from two attempts for the same task
    """
    if ignores is None:
        ignores = ['.*\.log', '.*\.json']
    good_summary = defaultdict(int)
    bad_summary = defaultdict(int)
    bad_list = []
    ignored = 0
    tups1 = list(os.walk(dir1))[0]
    tups2 = list(os.walk(dir2))[0]
    if not len(tups1[1]) == 0:
        raise ValueError('directory had unexpected subdirectories: "%s"' % dir1)
    if not len(tups2[1]) == 0:
        raise ValueError('directory had unexpected subdirectories: "%s"' % dir1)
    if len(tups1[2]) == 0:
        raise ValueError('directory had no files: "%s"' % dir1)
    if len(tups1[2]) != len(tups2[2]):
        raise ValueError('directories had different numbers of files: "%s" (%d), "%s" (%d)'
                         % (dir1, len(tups1[2]), dir2, len(tups2[3])))
    for file in tups1[2]:
        full1 = os.path.join(dir1, file)
        full2 = os.path.join(dir2, file)
        if not os.path.exists(full2):
            raise ValueError('Directory 2 lacks file "%s" present in directory 1' % file)
        skip_outer = False
        for ignore in ignores:
            if re.compile(ignore).match(file):
                ignored += 1
                skip_outer = True
                break
        if skip_outer:
            continue
        md5_1, md5_2 = md5(full1), md5(full2)
        if md5_1 == md5_2:
            good_summary[shorten(file)] += 1
        else:
            bad_summary[shorten(file)] += 1
            bad_list.append((full1, full2, md5_1, md5_2))
    return good_summary, bad_summary, bad_list, ignored


def summarize_compare_result(good_summary, bad_summary, bad_list, ignored):
    st = 'good summary:\n'
    for k, v in good_summary.items():
        st += '  %s: %d\n' % (k, v)
    st += 'bad summary:\n'
    for k, v in bad_summary.items():
        st += ('  %s: %d\n' % (k, v))
    if len(bad_list) > 0:
        st += 'bad list:\n'
        for f1, f2, _, _ in bad_list:  # ignore md5s
            st += ('  %s, %s\n' % (f1, f2))
    st += 'ignored: %d\n' % ignored
    return st


def sweep(basedir, ignores=None, quiet=True):
    attempt_re = re.compile('proj([\d]+)_input([\d]+)_attempt([\d]+)')
    proj_inputs = {}
    attempts = set()
    good_summary, bad_summary, bad_list, ignored = {}, {}, [], 0
    for root, dirs, files in os.walk(basedir):
        # First, look for attempt directories
        for dr in dirs:
            full_dir = os.path.join(root, dr)
            assert os.path.exists(full_dir) and os.path.isdir(full_dir)
            ma = attempt_re.match(dr)
            if ma is not None:
                done_fn = os.path.join(root, dr + '.done')
                if not os.path.exists(done_fn):
                    continue
                proj, inp, attempt = map(int, [ma.group(1), ma.group(2), ma.group(3)])
                assert (proj, inp, attempt) not in attempts
                attempts.add((proj, inp, attempt))
                if (proj, inp) in proj_inputs:
                    for prev_attempt in proj_inputs[(proj, inp)]:
                        if not quiet:
                            print('Trying %s == %s' % (full_dir, prev_attempt), file=sys.stderr)
                        my_good_summary, my_bad_summary, my_bad_list, my_ignored =\
                            compare(full_dir, prev_attempt, ignores=ignores)
                        good_summary.update(my_good_summary)
                        bad_summary.update(my_bad_summary)
                        bad_list += my_bad_list
                        ignored += my_ignored
                    proj_inputs[(proj, inp)].append(full_dir)
                else:
                    proj_inputs[(proj, inp)] = [full_dir]
    return good_summary, bad_summary, bad_list, ignored


def _put(fn, text):
    with open(fn, 'wt') as fh:
        fh.write(text)


def _put_both(dir1, dir2, fn, text):
    _put(os.path.join(dir1, fn), text)
    _put(os.path.join(dir2, fn), text)


def test_comapre_1():
    dir1 = tempfile.mkdtemp()
    dir2 = tempfile.mkdtemp()
    _put_both(dir1, dir2, 'test1.txt', 'hello\n')
    _put_both(dir1, dir2, 'test2.txt', 'world\n')
    good_summary, bad_summary, bad_list, ignored = compare(dir1, dir2)
    assert 2 == good_summary['txt']
    assert 0 == len(bad_summary)
    assert 0 == len(bad_list)
    assert 0 == ignored


def test_comapre_2():
    dir1 = tempfile.mkdtemp()
    dir2 = tempfile.mkdtemp()
    _put_both(dir1, dir2, 'test1.txt', 'hello\n')
    _put(os.path.join(dir1, 'test2.txt'), 'world1\n')
    _put(os.path.join(dir2, 'test2.txt'), 'world2\n')
    good_summary, bad_summary, bad_list, ignored = compare(dir1, dir2)
    assert 1 == good_summary['txt']
    assert 1 == len(bad_summary)
    assert 1 == len(bad_list)
    assert os.path.join(dir1, 'test2.txt') == bad_list[0][0]
    assert os.path.join(dir2, 'test2.txt') == bad_list[0][1]
    assert 0 == ignored


def test_comapre_3():
    dir1 = tempfile.mkdtemp()
    dir2 = tempfile.mkdtemp()
    _put_both(dir1, dir2, 'test1.txt', 'hello\n')
    _put(os.path.join(dir1, 'test2.log'), 'world1\n')
    _put(os.path.join(dir2, 'test2.log'), 'world2\n')
    _put(os.path.join(dir1, 'test3.json'), 'world1\n')
    _put(os.path.join(dir2, 'test3.json'), 'world1\n\n')
    good_summary, bad_summary, bad_list, ignored = compare(dir1, dir2)
    assert 1 == good_summary['txt']
    assert 1 == len(good_summary)
    assert 0 == len(bad_summary)
    assert 0 == len(bad_list)
    assert 2 == ignored


def test_sweep_1():
    dr = tempfile.mkdtemp()
    dir1 = os.path.join(dr, 'proj1_input1_attempt1')
    dir2 = os.path.join(dr, 'proj1_input1_attempt2')
    os.makedirs(dir1)
    os.makedirs(dir2)
    _put(dir1 + '.done', 'done\n')
    _put(dir2 + '.done', 'done\n')
    _put_both(dir1, dir2, 'test1.txt', 'hello\n')
    _put_both(dir1, dir2, 'test2.txt', 'world\n')
    good_summary, bad_summary, bad_list, ignored = sweep(dr)
    assert 2 == good_summary['txt']
    assert 0 == len(bad_summary)
    assert 0 == len(bad_list)
    assert 0 == ignored


def go():
    args = docopt(__doc__)

    if args['sweep']:
        good_summary, bad_summary, bad_list, ignored = sweep(args['<dir>'], quiet=False)
        print(summarize_compare_result(good_summary, bad_summary, bad_list, ignored))
    elif args['compare']:
        good_summary, bad_summary, bad_list, ignored = compare(args['<dir1>'], args['<dir2>'])
        print(summarize_compare_result(good_summary, bad_summary, bad_list, ignored))


if __name__ == '__main__':
    go()
