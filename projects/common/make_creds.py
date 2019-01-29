#!/usr/bin/env python

from __future__ import print_function
import os
import sys
import subprocess


def parse_project_ini(fn):
    options = {}
    with open(fn, 'rt') as fh:
        for ln in fh:
            ln = ln.rstrip()
            if len(ln) == 0 or ln[0] == '#':
                continue
            toks = ln.split('=')
            assert len(toks) >= 2
            if len(toks) > 2:
                toks[1] = '='.join(toks[1:])
            k, v = toks[0].strip(), toks[1].strip()
            if k in options:
                raise ValueError('key "%s" used more than once' % k)
            options[k] = v
    return options


def go():
    common_dirname = os.path.dirname(os.path.realpath(__file__))

    #
    # Run from project directory
    #

    print('Parsing public project conf', file=sys.stderr)
    public_conf_fn = 'public_conf.ini'
    if not os.path.exists(public_conf_fn):
        raise RuntimeError('Could not find public conf "%s"' % public_conf_fn)
    options = parse_project_ini(public_conf_fn)

    print('Parsing private project conf', file=sys.stderr)
    private_conf_fn = 'private_conf.ini'
    if not os.path.exists(private_conf_fn):
        raise RuntimeError('Could not find private conf "%s"' % private_conf_fn)
    options.update(parse_project_ini(private_conf_fn))

    cluster_dirname = os.path.join(common_dirname, 'clusters')
    cluster_scr = os.path.join(cluster_dirname, 'cluster.sh')
    p = subprocess.Popen([cluster_scr], shell=True, stdout=subprocess.PIPE)
    out, _ = p.communicate()
    clust_creds_dirname = None
    if p.returncode == 0:
        cluster_name = out.strip()
        print('Determined cluster is "%s"' % cluster_name, file=sys.stderr)
        clust_creds_dirname = os.path.join(cluster_dirname, cluster_name)
        
        if not os.path.exists(clust_creds_dirname):
            raise RuntimeError('No such cluster ini directory as "%s"' % clust_creds_dirname)

        print('Parsing private cluster conf', file=sys.stderr)
        private_clust_fn = os.path.join(cluster_dirname, 'private_conf.ini')
        if not os.path.exists(private_clust_fn):
            raise RuntimeError('Could not find private cluster conf "%s"' % private_clust_fn)
        options.update(parse_project_ini(private_clust_fn))
    else:
        print('Could not determine cluster', file=sys.stderr)

    print('Parsing project ini', file=sys.stderr)
    project_fn = 'project.ini'
    if not os.path.exists(project_fn):
        raise RuntimeError('Could not find project conf "%s"' % project_fn)
    options.update(parse_project_ini(project_fn))

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
                    if '%' in new_ln:
                        raise ValueError('Failed at least one substitution in line: %s' % new_ln)
                    ofh.write(new_ln)

    if clust_creds_dirname is not None:
        for fn in os.listdir(clust_creds_dirname):
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
                        if '%' in new_ln:
                            raise ValueError('Failed at least one substitution in line: %s' % new_ln)
                        ofh.write(new_ln)


if __name__ == '__main__':
    go()
