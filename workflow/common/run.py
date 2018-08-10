#!/usr/bin/env python

from __future__ import print_function
import os
import sys
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
    if os.path.exists(os.path.join(dr, name)):
        raise RuntimeError('Directory "%s" already exists' % dr)


def to_docker_env(cmd_env):
    return ' '.join(map(lambda x: '-e "%s"' % x, cmd_env))


def to_singularity_env(cmd_env):
    return '; '.join(cmd_env) + '; '


def go(args):
    print('Job name: "%s"' % args.name, file=sys.stderr)
    print('Image: "%s"' % args.image, file=sys.stderr)
    if not os.path.exists(args.ini):
        raise RuntimeError('No such ini file "%s"' % args.ini)
    cfg = RawConfigParser()
    cfg.read(args.ini)
    section = cfg.sections()[0]
    print('Reading section [%s] from ini "%s"' % (section, args.ini), file=sys.stderr)
    input_base = cfg.get(section, 'input_base')
    output_base = cfg.get(section, 'output_base')
    ref_base = cfg.get(section, 'ref_base')
    temp_base = cfg.get(section, 'temp_base')

    system = 'singularity' if args.singularity else 'docker'
    if cfg.has_option(section, 'system'):
        system = cfg.get(section, 'system')
        if system not in ['singularity', 'docker']:
            raise ValueError('Bad container system: "%s"' % system)

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

    print('Input base: "%s"' % input_base, file=sys.stderr)
    print('Output base: "%s"' % output_base, file=sys.stderr)
    print('Reference base: "%s"' % ref_base, file=sys.stderr)
    print('Temp base: "%s"' % temp_base, file=sys.stderr)

    subdir_clear(input_base, args.name)
    subdir_clear(output_base, args.name)
    subdir_clear(temp_base, args.name)

    input_mount = cfg.get(section, 'input_mount')
    output_mount = cfg.get(section, 'output_mount')
    ref_mount = cfg.get(section, 'ref_mount')
    temp_mount = cfg.get(section, 'temp_mount')

    mounts = []
    docker = system == 'docker'
    if input_mount is not None:
        mounts.append('-v' if docker else '-B')
        mounts.append('%s/%s:%s' % (input_base, args.name, input_mount))
    else:
        input_mount = os.path.join(input_base, args.name)
    os.makedirs(os.path.join(input_base, args.name))
    for inp in args.input:
        shutil.copy2(inp, os.path.join(input_base, args.name, os.path.basename(inp)))
    if output_mount is not None:
        mounts.append('-v' if docker else '-B')
        mounts.append('%s/%s:%s' % (output_base, args.name, output_mount))
    else:
        output_mount = os.path.join(output_base, args.name)
    os.makedirs(os.path.join(output_base, args.name))
    if temp_mount is not None:
        mounts.append('-v' if docker else '-B')
        mounts.append('%s/%s:%s' % (temp_base, args.name, temp_mount))
    else:
        temp_mount = os.path.join(temp_base, args.name)
    os.makedirs(os.path.join(temp_base, args.name))
    if ref_mount is not None:
        mounts.append('-v' if docker else '-B')
        mounts.append('%s:%s' % (ref_base, ref_mount))
    else:
        ref_mount = ref_base

    cmd_env = ['RECOUNT_JOB_ID=%s' % args.name,
               'RECOUNT_INPUT=%s' % input_mount,
               'RECOUNT_OUTPUT=%s' % output_mount,
               'RECOUNT_TEMP=%s' % temp_mount,
               'RECOUNT_REF=%s' % ref_mount]
    cmd_run = '/bin/bash -c "source activate recount && bash /workflow.bash"'
    if docker:
        cmd = 'docker run %s %s %s %s' % (to_docker_env(cmd_env), ' '.join(mounts), args.image, cmd_run)
    else:
        cmd = '%s singularity exec %s %s %s' % (to_singularity_env(cmd_env), ' '.join(mounts), args.image, cmd_run)
    print(cmd, file=sys.stderr)
    ret = os.system(cmd)

    if ret == 0 and not args.keep:
        print('Removing input & temporary directories', file=sys.stderr)
        shutil.rmtree(os.path.join(input_base, args.name))
        shutil.rmtree(os.path.join(temp_base, args.name))

    print('SUCCESS' if ret == 0 else 'FAILURE', file=sys.stderr)
    sys.exit(ret)


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
