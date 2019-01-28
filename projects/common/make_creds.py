#!/usr/bin/env python

from __future__ import print_function
import os


def parse_project_ini(fn):
    options = {}
    with open(fn, 'rt') as fh:
        for ln in fh:
            ln = ln.rstrip()
            if len(ln) == 0 or ln[0] == '#':
                continue
            toks = ln.split('=')
            assert 2 == len(toks)
            k, v = toks[0].strip(), toks[1].strip()
            if k in options:
                raise ValueError('key "%s" used more than once' % k)
            options[k] = v
    return options


def go():
    common_dirname = os.path.dirname(os.path.realpath(__file__))

    public_conf_fn = 'public_conf.ini'
    if not os.path.exists(public_conf_fn):
        raise RuntimeError('Could not find public conf "%s"' % public_conf_fn)
    options = parse_project_ini(public_conf_fn)

    private_conf_fn = 'private_conf.ini'
    if not os.path.exists(private_conf_fn):
        raise RuntimeError('Could not find private conf "%s"' % private_conf_fn)
    options.update(parse_project_ini(private_conf_fn))

    creds_dirname = os.path.join(common_dirname, 'creds')
    if not os.path.exists(creds_dirname):
        raise RuntimeError('No such creds template dir as "%s"' % creds_dirname)

    if os.path.exists('creds'):
        raise RuntimeError('Local "creds" directory (or file) already exists')

    os.makedirs('creds')
    for fn in os.listdir(creds_dirname):
        template_fn = os.path.join(creds_dirname, fn)
        new_fn = os.path.join('creds', fn)
        with open(new_fn, 'wt') as ofh:
            with open(template_fn, 'rt') as fh:
                for ln in fh:
                    new_ln = ln
                    for k, v in options.items():
                        kvar = '%' + k + '%'
                        if kvar in new_ln:
                            new_ln = new_ln.replace(kvar, v)
                    ofh.write(new_ln)


if __name__ == '__main__':
    go()
