#!/usr/bin/env python

# Author: Ben Langmead <ben.langmead@gmail.com>
# License: MIT

"""run

Usage:
  run go <name> <image-url> <image-fn> <config> <input>... [options]

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
import json
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


def log_info(msg, queue):
    if queue is None:
        log.info(msg, 'run.py')
    else:
        queue.put((msg, 'run.py'))


def log_info_detailed(node_name, worker_name, msg, queue):
    log_info(' '.join([node_name, worker_name, msg]), queue)


def decode(st):
    return st if isinstance(st, str) else st.decode()


def reader(node_name, worker_name, pipe, queue, nm):
    if queue is None:
        for line in pipe:
            msg = ' '.join([node_name, worker_name, nm, decode(line.rstrip())])
            log.info(msg, 'run.py')
    else:
        for line in pipe:
            msg = ' '.join([node_name, worker_name, nm, decode(line.rstrip())])
            queue.put((msg, 'run.py'))


def run_job(name, inputs, image_url, image_fn, config, cluster_ini,
            keep=False, mover=None, destination=None, source_prefix=None,
            log_queue=None, node_name='', worker_name=''):
    log_info_detailed(node_name, worker_name, 'job name: %s, image-url: "%s", image-fn: "%s"' %
                      (name, image_url, image_fn), log_queue)
    if not os.path.exists(cluster_ini):
        raise RuntimeError('No such ini file "%s"' % cluster_ini)
    cfg = RawConfigParser()
    cfg.read(cluster_ini)
    section = cfg.sections()[0]
    log_info_detailed(node_name, worker_name, 'reading section %s from ini %s' % (section, cluster_ini), log_queue)
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

    log_info_detailed(node_name, worker_name, 'inputs: ' + str(inputs), log_queue)
    log_info_detailed(node_name, worker_name, 'using %s as container system' % system, log_queue)
    log_info_detailed(node_name, worker_name, 'using sudo: %s' % str(sudo), log_queue)
    log_info_detailed(node_name, worker_name, 'using %d cpus' % cpus, log_queue)

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

    log_info_detailed(node_name, worker_name, 'input base: ' + input_base, log_queue)
    log_info_detailed(node_name, worker_name, 'output base: ' + output_base, log_queue)
    log_info_detailed(node_name, worker_name, 'reference base: ' + ref_base, log_queue)
    log_info_detailed(node_name, worker_name, 'temp base: ' + temp_base, log_queue)

    subdir_clear(input_base, name)
    subdir_clear(output_base, name)
    subdir_clear(temp_base, name)

    input_mount = cfg.get(section, 'input_mount')
    output_mount = cfg.get(section, 'output_mount')
    ref_mount = cfg.get(section, 'ref_mount')
    temp_mount = cfg.get(section, 'temp_mount')

    mounts = []
    docker = system == 'docker'

    # Input
    input_base_name = os.path.join(input_base, name)
    if input_mount is not None and len(input_mount) > 0:
        mounts.append('-v' if docker else '-B')
        mounts.append('%s:%s' % (input_base_name, input_mount))
    else:
        input_mount = input_base_name
    os.makedirs(input_base_name)
    for inp in inputs:
        assert os.path.exists(inp)
        dest = os.path.join(input_base_name, os.path.basename(inp))
        shutil.copy2(inp, dest)
        assert os.path.exists(dest)
    staged_inputs = [f for f in os.listdir(input_base_name) if os.path.isfile(os.path.join(input_base_name, f))]
    assert len(staged_inputs) > 0, (input_base_name, input_mount, inputs)
    log_info_detailed(node_name, worker_name, 'staged inputs: ' + str(staged_inputs), log_queue)

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
    temp_base_name = os.path.join(temp_base, name)
    os.makedirs(temp_base_name)
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

    # copy config into input directory
    assert os.path.exists(temp_base_name) and os.path.isdir(temp_base_name)
    config_fn = os.path.join(temp_base_name, 'config.json')
    with open(config_fn, 'wt') as fh:
        fh.write(json.dumps(json.loads(config), indent=4))

    log_info('COUNT_RunWorkflowPre 1', log_queue)

    image = image_url
    if docker:
        if image.startswith('docker://'):
            image = image[len('docker://'):]
        cmd = 'docker'
        if sudo:
            cmd = 'sudo ' + cmd
        cmd += (' run %s %s %s %s' % (to_docker_env(cmd_env), ' '.join(mounts), image, cmd_run))
    else:
        if image_fn is not None and os.path.exists(image_fn):
            image = image_fn
        cmd = '%s singularity exec %s %s %s' % (to_singularity_env(cmd_env), ' '.join(mounts), image, cmd_run)
    log_info_detailed(node_name, worker_name, 'command: ' + cmd, log_queue)
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

    if ret != 0:
        raise RuntimeError('Container returned non-zero exitlevel %d' % ret)

    log_info('COUNT_RunWorkflowPost 1', log_queue)

    # Copy files to ultimate destination, if one is specified
    extras = ['stats.json']
    if mover is not None and destination is not None and len(destination) > 0:
        if source_prefix is None or len(source_prefix) == 0:
            source_prefix = 'local://'
        output_dir = os.path.join(output_base, name)
        log_info_detailed(node_name, worker_name,
                          'using mover to copy outputs from "%s" to "%s"' %
                          (output_dir, destination), log_queue)
        for fn in os.listdir(output_dir):
            manifest_ext = '.manifest'
            if fn.endswith(manifest_ext):
                srr = fn[:-len(manifest_ext)]
                fn = os.path.join(output_dir, fn)
                log_info_detailed(node_name, worker_name,
                                  'found manifest "%s" for %s'
                                  % (fn, srr), log_queue)
                with open(fn, 'rt') as man_fh:
                    xfers = []
                    tot_sz = 0
                    for xfer_fn in man_fh.read().split():
                        full_xfer_fn = os.path.join(output_dir, xfer_fn)
                        sz = os.path.getsize(full_xfer_fn)
                        log_info_detailed(node_name, worker_name,
                                          'moving file "%s" of size %d' %
                                          (full_xfer_fn, sz), log_queue)
                        if not os.path.exists(full_xfer_fn):
                            raise RuntimeError('File "%s" was in manifest ("%s") '
                                               'but was not present in output '
                                               'directory' % (full_xfer_fn, fn))
                        xfers.append(xfer_fn)
                        tot_sz += sz
                    for extra in extras:
                        full_extra = os.path.join(output_dir, extra)
                        if os.path.exists(full_extra):
                            sz = os.path.getsize(full_extra)
                            log_info_detailed(node_name, worker_name,
                                              'found extra file "%s" of size %d' %
                                              (full_extra, sz), log_queue)
                            new_name = srr + '.' + extra
                            new_name_full = os.path.join(output_dir, new_name)
                            os.rename(full_extra, new_name_full)
                            assert os.path.exists(new_name_full)
                            xfers.append(new_name)
                            tot_sz += sz
                        else:
                            log_info_detailed(node_name, worker_name,
                                              'could not find extra file "%s"'
                                              % extra, log_queue)
                    log_info_detailed(node_name, worker_name,
                                      'Moving files of total size %d b: %s'
                                      % (tot_sz, str(xfers)), log_queue)
                    log_info('COUNT_DestXferPre 1', log_queue)
                    mover.multi(source_prefix + output_dir, destination, xfers)
                    log_info('COUNT_DestXferPost 1', log_queue)
                    log_info_detailed(node_name, worker_name,
                                      'Finished moving %d files of total size %d'
                                      % (len(xfers), tot_sz), log_queue)
                    log_info('COUNT_DestBytesMoved %d' % tot_sz, log_queue)
                    log_info('COUNT_DestFilesMoved %d' % len(xfers), log_queue)

        if not keep:
            shutil.rmtree(output_dir)

    print('SUCCESS' if ret == 0 else 'FAILURE', file=sys.stderr)
    return ret == 0


def go():
    args = docopt(__doc__)
    log_ini = os.path.expanduser(args['--log-ini'])
    log.init_logger(log.LOG_GROUP_NAME, log_ini=log_ini, agg_level=args['--log-level'])
    cluster_ini = os.path.expanduser(args['--cluster-ini'])
    try:
        if args['go']:
            config = args['<config>']
            if config.startswith('file://'):
                config = config[7:]
                if not os.path.exists(config):
                    raise RuntimeError('No such config file: "%s"' % config)
                with open(config, 'rt') as fh:
                    config = fh.read()

            run_job(args['<name>'], args['<input>'], args['<image-url>'],
                    args['<image-fn>'], config, cluster_ini,
                    keep=args['--keep'])
    except Exception:
        log.error('Uncaught exception:', 'run.py')
        raise


if __name__ == '__main__':
    go()
