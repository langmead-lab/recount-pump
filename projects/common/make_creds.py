#!/usr/bin/env python

"""
Instantiates a project on a particular cluster.

Run this from a project directory.  The cluster identity will be inferred
automatically.   If the required configurations are not available for this
cluster, an error will be emitted.
"""

from __future__ import print_function
import os
import sys
import subprocess
import copy


# TODO: set umask

def parse_project_ini(fn, options):
    with open(fn, 'rt') as fh:
        for ln in fh:
            ln = ln.rstrip()
            if len(ln) == 0 or ln[0] == '#':
                continue
            if '+=' in ln:
                # handle append
                toks = ln.split('+=')
                assert len(toks) >= 2
                if len(toks) > 2:
                    toks[1] = '+='.join(toks[1:])
                k, v = toks[0].strip(), toks[1].strip()
                if k in options:
                    # add to existing
                    options[k].append(v)
                else:
                    # make new
                    options[k] = [v]
            else:
                # handle set
                toks = ln.split('=')
                assert len(toks) >= 2
                if len(toks) > 2:
                    toks[1] = '='.join(toks[1:])
                k, v = toks[0].strip(), toks[1].strip()
                if k in options:
                    raise ValueError('key "%s" used more than once' % k)
                options[k] = v


def go():
    common_dirname = os.path.dirname(os.path.realpath(__file__))

    #
    # Run from project directory
    #

    print('Parsing public project conf', file=sys.stderr)
    public_conf_fn = 'public_conf.ini'
    if not os.path.exists(public_conf_fn):
        raise RuntimeError('Could not find public conf "%s"' % public_conf_fn)
    options = {}
    parse_project_ini(public_conf_fn, options)

    print('Parsing private project conf', file=sys.stderr)
    private_conf_fn = 'private_conf.ini'
    if not os.path.exists(private_conf_fn):
        raise RuntimeError('Could not find private conf "%s"' % private_conf_fn)
    parse_project_ini(private_conf_fn, options)

    top_cluster_dirname = os.path.join(common_dirname, 'clusters')
    cluster_scr = os.path.join(top_cluster_dirname, 'cluster.sh')
    p = subprocess.Popen([cluster_scr], shell=True, stdout=subprocess.PIPE)
    out, _ = p.communicate()
    cluster_name, clust_dirname = None, None
    if p.returncode == 0:
        cluster_name = out.strip().decode()
        print('Determined cluster is "%s"' % cluster_name, file=sys.stderr)
        clust_dirname = os.path.join(top_cluster_dirname, cluster_name)

        if not os.path.exists(clust_dirname):
            raise RuntimeError('No such cluster ini directory as "%s"' % clust_dirname)

        print('Parsing public cluster conf', file=sys.stderr)
        public_clust_fn = os.path.join(clust_dirname, 'public_conf.ini')
        if not os.path.exists(public_clust_fn):
            raise RuntimeError('Could not find public cluster conf "%s"' % public_clust_fn)
        parse_project_ini(public_clust_fn, options)

        print('Parsing private cluster conf', file=sys.stderr)
        private_clust_fn = os.path.join(clust_dirname, 'private_conf.ini')
        if not os.path.exists(private_clust_fn):
            raise RuntimeError('Could not find private cluster conf "%s"' % private_clust_fn)
        parse_project_ini(private_clust_fn, options)

        # Per-partition confs are left for loop below

    else:
        print('Could not determine cluster', file=sys.stderr)

    print('Parsing project ini', file=sys.stderr)
    project_fn = 'project.ini'
    if not os.path.exists(project_fn):
        raise RuntimeError('Could not find project conf "%s"' % project_fn)
    parse_project_ini(project_fn, options)

    creds_dirname = os.path.join(common_dirname, 'creds')
    if not os.path.exists(creds_dirname):
        raise RuntimeError('No such creds template dir as "%s"' % creds_dirname)

    if os.path.exists('creds'):
        raise RuntimeError('Local "creds" directory (or file) already exists')

    #
    # Generate project-specific ini files
    # Includes: db.ini, queue.ini, s3.ini, log.ini
    #

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

    #
    # Generate cluster-specific ini files
    # (might also have some project specificity)
    # Includes: destination.ini, globus.ini
    #

    if clust_dirname is not None:
        print('Working on inis for cluster "%s"' % cluster_name, file=sys.stderr)
        creds_output = os.path.join(clust_dirname, 'creds')
        n = 0
        for fn in os.listdir(creds_output):
            if os.path.isdir(fn) or not fn.endswith('.ini'):
                continue
            n += 1
            template_fn = os.path.join(creds_output, fn)  # input file
            new_fn = os.path.join('creds', fn)            # output file
            with open(new_fn, 'wt') as ofh:
                with open(template_fn, 'rt') as fh:
                    for ln in fh:
                        new_ln = ln
                        for k, v in options.items():
                            if not isinstance(v, list):
                                kvar = '%' + k + '%'
                                if kvar in new_ln:
                                    new_ln = new_ln.replace(kvar, v)
                        if '%' in new_ln:
                            raise ValueError('Failed at least one substitution in line: %s' % new_ln)
                        ofh.write(new_ln)

        if n == 0:
            raise RuntimeError('No ini files in dir "%s"' % creds_output)

        #
        # Generate partition-specific ini files and scripts
        # Includes: cluster-<partition>.ini, job-<partition>.sh
        #

        n = 0
        for fn in os.listdir(clust_dirname):
            if fn == 'creds':
                continue
            full_fn = os.path.join(clust_dirname, fn)
            if not os.path.isdir(full_fn):
                continue
            n += 1
            partition = fn
            print('  Working on ini/sh for cluster/partition "%s/%s"' % (cluster_name, partition), file=sys.stderr)

            print('Parsing partition conf for "%s/%s"' % (cluster_name, partition), file=sys.stderr)
            part_fn = os.path.join(clust_dirname, fn, 'partition.ini')
            if not os.path.exists(part_fn):
                raise RuntimeError('No partition.ini file in "%s/%s"' % (clust_dirname, fn))
            part_options = copy.deepcopy(options)
            parse_project_ini(part_fn, part_options)

            part_ini_fn = os.path.join('creds', 'cluster-%s.ini' % partition)
            with open(part_ini_fn, 'wt') as fh:
                fh.write('[cluster]\n')
                for k, v in sorted(part_options.items()):
                    if k.startswith('cluster_') and not isinstance(v, list):
                        fh.write('%s=%s\n' % (k[len('cluster_'):], v))

            job_sh_fn = os.path.join('creds', 'job-%s.sh' % partition)
            with open(job_sh_fn, 'wt') as fh:
                assert 'cluster_job_header' in part_options
                assert 'cluster_pump_dir' in part_options
                head = part_options['cluster_job_header']
                fh.write('\n'.join(head) + '\n\n')
                cluster_py = os.path.join(part_options['cluster_pump_dir'], 'src', 'cluster.py')
                # TODO: assumes project id is 1
                fh.write('umask 0077')  # conservative umask
                fh.write('python %s run --ini-base creds --cluster-ini %s %s\n' %
                         (cluster_py, part_ini_fn, options['study']))

            prep_sh_fn = os.path.join('creds', 'prep-%s.sh' % partition)
            with open(prep_sh_fn, 'wt') as fh:
                assert 'cluster_prep_header' in part_options
                head = part_options['cluster_prep_header']
                fh.write('\n'.join(head) + '\n\n')
                cluster_py = os.path.join(part_options['cluster_pump_dir'], 'src', 'cluster.py')
                # TODO: assumes project id is 1
                fh.write('umask 0077')  # conservative umask
                fh.write('python %s prepare --ini-base creds --cluster-ini %s %s\n' %
                         (cluster_py, part_ini_fn, options['study']))

        if n == 0:
            raise RuntimeError('No subdirectories in "%s"' % clust_dirname)


if __name__ == '__main__':
    go()
