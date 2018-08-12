#!/usr/bin/env python

from __future__ import print_function
import os
import sys
import log
import shutil
import argparse
try:
    from configparser import RawConfigParser
except ImportError:
    from ConfigParser import RawConfigParser


def isdir(dr):
    if not os.path.exists(dr) or not os.path.isdir(dr):
        raise RuntimeError('Does not exist or is not a directory: "%s"' % dr)


def subdir_clear(dr, name):
    subdir = os.path.join(dr, name)
    if os.path.exists(subdir):
        raise RuntimeError('Subdirectory "%s" already exists' % subdir)


def to_docker_env(cmd_env):
    return ' '.join(map(lambda x: '-e "%s"' % x, cmd_env))


def to_singularity_env(cmd_env):
    return '; '.join(map(lambda x: 'export ' + x, cmd_env)) + '; '


def run_job(name, inputs, image, cluster_ini, singularity=True, keep=False):
    log.info('job name: %s, image: "%s"' % (name, image), 'run.py')
    if not os.path.exists(cluster_ini):
        raise RuntimeError('No such ini file "%s"' % cluster_ini)
    cfg = RawConfigParser()
    cfg.read(cluster_ini)
    section = cfg.sections()[0]
    log.info('reading section %s from ini %s' % (section, cluster_ini), 'run.py')
    input_base = cfg.get(section, 'input_base')
    output_base = cfg.get(section, 'output_base')
    ref_base = cfg.get(section, 'ref_base')
    temp_base = cfg.get(section, 'temp_base')

    system = 'singularity' if singularity else 'docker'
    if cfg.has_option(section, 'system'):
        system = cfg.get(section, 'system')
        if system not in ['singularity', 'docker']:
            raise ValueError('Bad container system: "%s"' % system)

    log.info('using %s as container system' % singularity, 'run.py')

    if not os.path.exists(input_base):
        os.makedirs(input_base)
    elif not os.path.isdir(input_base):
        raise RuntimeError('input_base "%s" exists but is not a directory' % input_base)
    if not os.path.exists(output_base):
        os.makedirs(output_base)
    elif not os.path.isdir(output_base):
        raise RuntimeError('output_base "%s" exists but is not a directory' % output_base)
    if not os.path.exists(temp_base):
        os.makedirs(temp_base)
    elif not os.path.isdir(temp_base):
        raise RuntimeError('temp_base "%s" exists but is not a directory' % temp_base)
    isdir(ref_base)

    log.info('input base: ' + input_base, 'run.py')
    log.info('output base: ' + output_base, 'run.py')
    log.info('reference base: ' + ref_base, 'run.py')
    log.info('temp base: ' + temp_base, 'run.py')

    subdir_clear(input_base, name)
    subdir_clear(output_base, name)
    subdir_clear(temp_base, name)

    input_mount = cfg.get(section, 'input_mount')
    output_mount = cfg.get(section, 'output_mount')
    ref_mount = cfg.get(section, 'ref_mount')
    temp_mount = cfg.get(section, 'temp_mount')

    mounts = []
    docker = system == 'docker'
    if input_mount is not None:
        mounts.append('-v' if docker else '-B')
        mounts.append('%s/%s:%s' % (input_base, name, input_mount))
    else:
        input_mount = os.path.join(input_base, name)
    os.makedirs(os.path.join(input_base, name))
    for inp in inputs:
        shutil.copy2(inp, os.path.join(input_base, name, os.path.basename(inp)))
    if output_mount is not None:
        mounts.append('-v' if docker else '-B')
        mounts.append('%s/%s:%s' % (output_base, name, output_mount))
    else:
        output_mount = os.path.join(output_base, name)
    os.makedirs(os.path.join(output_base, name))
    if temp_mount is not None:
        mounts.append('-v' if docker else '-B')
        mounts.append('%s/%s:%s' % (temp_base, name, temp_mount))
    else:
        temp_mount = os.path.join(temp_base, name)
    os.makedirs(os.path.join(temp_base, name))
    if ref_mount is not None:
        mounts.append('-v' if docker else '-B')
        mounts.append('%s:%s' % (ref_base, ref_mount))
    else:
        ref_mount = ref_base

    cmd_env = ['RECOUNT_JOB_ID=%s' % name,
               'RECOUNT_INPUT=%s' % input_mount,
               'RECOUNT_OUTPUT=%s' % output_mount,
               'RECOUNT_TEMP=%s' % temp_mount,
               'RECOUNT_REF=%s' % ref_mount]
    cmd_run = '/bin/bash -c "source activate recount && bash /workflow.bash"'
    if docker:
        cmd = 'docker run %s %s %s %s' % (to_docker_env(cmd_env), ' '.join(mounts), image, cmd_run)
    else:
        cmd = '%s singularity exec %s %s %s' % (to_singularity_env(cmd_env), ' '.join(mounts), image, cmd_run)
    log.info('command: ' + cmd, 'run.py')
    print(cmd, file=sys.stderr)
    ret = os.system(cmd)

    if ret == 0 and not keep:
        print('Removing input & temporary directories', file=sys.stderr)
        shutil.rmtree(os.path.join(input_base, name))
        shutil.rmtree(os.path.join(temp_base, name))

    print('SUCCESS' if ret == 0 else 'FAILURE', file=sys.stderr)
    return ret == 0


def go(args):
    run_job(args.name, args.input, args.image, args.ini, args.singularity, args.keep)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__,
            formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--name', type=str, required=True,
                        help='job name, which determines subdirectory names')
    parser.add_argument('--image', type=str, required=True,
                        help='image to use with "singularity exec" or "docker run"')
    parser.add_argument('--input', type=str, required=True, nargs='+',
                        help='input files')
    parser.add_argument('--ini', type=str,
                        default=os.path.expanduser('~/.recount/cluster.ini'),
                        help='path to cluster.ini file')
    parser.add_argument('--keep', type=bool, default=False,
                        help='do not remove temp and input directories upon success')
    parser.add_argument('--docker', action='store_true', help='image ')
    parser.add_argument('--singularity', action='store_true', help='print this message')
    go(parser.parse_args(sys.argv[1:]))
