#!/usr/bin/env python

# Author: Ben Langmead <ben.langmead@gmail.com>
# License: MIT

"""run

Usage:
  run go <name> <image> <input>... [options]

Options:
  <name>                   Job name, used for subdirectory names
  <image>                  Image to run.  Can be docker:// URL.
  <input>                  Image to run.  Can be docker:// URL.
  --cluster-ini <ini>      ini file for cluster [default: ~/.recount/cluster.ini].
  --log-ini <ini>          ini file for log aggregator [default: ~/.recount/log.ini].
  --log-level <level>      set level for log aggregation; could be CRITICAL,
                           ERROR, WARNING, INFO, DEBUG [default: INFO].
  --keep                   Do not remove temp and input directories upon success
  -h, --help               Show this screen.
  --version                Show version.
"""

from __future__ import print_function
import os
import sys
import log
import shutil
from docopt import docopt
import subprocess
import threading
if sys.version[:1] == '2':
    from ConfigParser import RawConfigParser
else:
    from configparser import RawConfigParser

"""
Run a workflow in a container.  Can use either Docker or Singularity.  Sets up
directories and mounting patterns so that workflow can interact with host
filesystem in predictable ways.
"""


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


def reader(node_name, worker_name, pipe, queue, nm):
    with pipe:
        if queue is None:
            for line in pipe:
                log.info(' '.join([node_name, worker_name, nm, line.rstrip()]), 'run.py')
        else:
            for line in pipe:
                queue.put((node_name, worker_name, nm, line.rstrip()))


def run_job(name, inputs, image, cluster_ini,
            keep=False, mover=None, destination=None,
            log_queue=None, node_name='', worker_name=''):
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
    system = 'docker'
    if cfg.has_option(section, 'system'):
        system = cfg.get(section, 'system')
        if system not in ['singularity', 'docker']:
            raise ValueError('Bad container system: "%s"' % system)
    cpus = 1
    if cfg.has_option(section, 'cpus'):
        cpus = int(cfg.get(section, 'cpus'))
        if cpus < 1:
            raise ValueError('# cpus specified --cluster-ini must be >= 0; was %d' % cpus)
    sudo = False
    if cfg.has_option(section, 'sudo'):
        sudo = cfg.get(section, 'sudo').lower() == 'true'

    log.info('using %s as container system' % system, 'run.py')
    log.info('using sudo: %s' % str(sudo), 'run.py')
    log.info('using %d cpus' % cpus, 'run.py')

    if not os.path.exists(input_base):
        try:
            os.makedirs(input_base)
        except FileExistsError:
            pass
    elif not os.path.isdir(input_base):
        raise RuntimeError('input_base "%s" exists but is not a directory' % input_base)
    if not os.path.exists(output_base):
        try:
            os.makedirs(output_base)
        except FileExistsError:
            pass
    elif not os.path.isdir(output_base):
        raise RuntimeError('output_base "%s" exists but is not a directory' % output_base)
    if not os.path.exists(temp_base):
        try:
            os.makedirs(temp_base)
        except FileExistsError:
            pass
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
    if input_mount is not None and len(input_mount) > 0:
        mounts.append('-v' if docker else '-B')
        mounts.append('%s/%s:%s' % (input_base, name, input_mount))
    else:
        input_mount = os.path.join(input_base, name)
    os.makedirs(os.path.join(input_base, name))
    for inp in inputs:
        shutil.copy2(inp, os.path.join(input_base, name, os.path.basename(inp)))
    if output_mount is not None and len(output_mount) > 0:
        mounts.append('-v' if docker else '-B')
        mounts.append('%s/%s:%s' % (output_base, name, output_mount))
    else:
        output_mount = os.path.join(output_base, name)
    os.makedirs(os.path.join(output_base, name))
    if temp_mount is not None and len(temp_mount) > 0:
        mounts.append('-v' if docker else '-B')
        mounts.append('%s/%s:%s' % (temp_base, name, temp_mount))
    else:
        temp_mount = os.path.join(temp_base, name)
    os.makedirs(os.path.join(temp_base, name))
    if ref_mount is not None and len(ref_mount) > 0:
        mounts.append('-v' if docker else '-B')
        mounts.append('%s:%s' % (ref_base, ref_mount))
    else:
        ref_mount = ref_base
    cmd_env = ['RECOUNT_JOB_ID=%s' % name,
               'RECOUNT_INPUT=%s' % input_mount,
               'RECOUNT_OUTPUT=%s' % output_mount,
               'RECOUNT_TEMP=%s' % temp_mount,
               'RECOUNT_CPUS=%d' % cpus,
               'RECOUNT_REF=%s' % ref_mount]
    cmd_run = '/bin/bash -c "source activate recount && bash /workflow.bash"'
    if docker:
        cmd = 'docker'
        if sudo:
            cmd = 'sudo ' + cmd
        cmd += (' run %s %s %s %s' % (to_docker_env(cmd_env), ' '.join(mounts), image, cmd_run))
    else:
        cmd = '%s singularity exec %s %s %s' % (to_singularity_env(cmd_env), ' '.join(mounts), image, cmd_run)
    log.info('command: ' + cmd, 'run.py')
    proc = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    t_out = threading.Thread(target=reader,
                             args=[node_name, worker_name, proc.stdout, log_queue, 'out'])
    t_err = threading.Thread(target=reader,
                             args=[node_name, worker_name, proc.stderr, log_queue, 'err'])
    t_out.start()
    t_err.start()
    t_out.join()
    t_err.join()
    proc.wait()
    ret = proc.returncode
    if ret == 0 and not keep:
        print('Removing input & temporary directories', file=sys.stderr)
        shutil.rmtree(os.path.join(input_base, name))
        shutil.rmtree(os.path.join(temp_base, name))

    if mover is not None and destination is not None and len(destination) > 0:
        output_dir = os.path.join(output_base, name)
        log.info('using mover to copy outputs from "%s" to "%s"' % (output_dir, destination), 'run.py')
        for fn in os.listdir(output_dir):
            if fn.endswith('.manifest'):
                log.info('found manifest "%s"' % fn, 'run.py')
                with open(fn, 'rt') as man_fh:
                    files = man_fh.read().split()
                    for file in files:
                        sz = os.path.getsize(file)
                        log.info('moving file "%s" of size %d' % (fn, sz), 'run.py')
                        if not os.path.exists(file):
                            raise RuntimeError('File "%s" was in manifest ("%s") '
                                               'but was not present in output '
                                               'directory' % (file, fn))
                    mover.multi(output_base, destination, files)

    print('SUCCESS' if ret == 0 else 'FAILURE', file=sys.stderr)
    return ret == 0


def go():
    args = docopt(__doc__)
    log_ini = os.path.expanduser(args['--log-ini'])
    log.init_logger(log.LOG_GROUP_NAME, log_ini=log_ini, agg_level=args['--log-level'])
    cluster_ini = os.path.expanduser(args['--cluster-ini'])
    try:
        if args['go']:
            run_job(args['<name>'], args['<input>'], args['<image>'], cluster_ini,
                    keep=args['--keep'])
    except Exception:
        log.error('Uncaught exception:', 'run.py')
        raise


if __name__ == '__main__':
    go()
