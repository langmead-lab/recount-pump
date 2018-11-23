#!/usr/bin/env python

# Author: Ben Langmead <ben.langmead@gmail.com>
# License: MIT

import os
import sys
import hashlib
import subprocess
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from base import Base

if sys.version[:1] == '2':
    from ConfigParser import RawConfigParser
else:
    from configparser import RawConfigParser


def generate_file_md5(fn, blocksize=2**20):
    """
    Return md5 checksum of file; based on:
    https://stackoverflow.com/questions/1131220/get-md5-hash-of-big-files-in-python
    """
    m = hashlib.md5()
    with open(fn, "rb") as f:
        while True:
            buf = f.read(blocksize)
            if not buf:
                break
            m.update(buf)
    return m.hexdigest()


def engine_from_config(fn, section='client', echo=False):
    config = RawConfigParser(allow_no_value=True)
    if not os.path.exists(fn):
        raise RuntimeError('No such ini file: "%s"' % fn)
    config.read(fn)
    engine_url = config.get(section, "url")
    return create_engine(engine_url, echo=echo)


def session_maker_from_config(fn, section='client', echo=False):
    engine = engine_from_config(fn, section=section, echo=echo)
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine)


def parse_queue_config(fn, section='queue'):
    cfg = RawConfigParser(allow_no_value=True)
    if not os.path.exists(fn):
        raise RuntimeError('No such ini file: "%s"' % fn)
    cfg.read(fn)

    def _get_option(nm):
        if not cfg.has_option(section, nm):
            return None
        opt = cfg.get(section, nm)
        return None if (len(opt) == 0) else opt

    return _get_option('aws_profile'), _get_option('region'), _get_option('endpoint')


def md5(fn):
    image_md5 = subprocess.check_output(['md5sum', fn])
    return image_md5.decode().split()[0]


def which(program):
    def is_exe(fp):
        return os.path.isfile(fp) and os.access(fp, os.X_OK)

    fpath, fname = os.path.split(program)
    if fpath:
        if is_exe(program):
            return program
    else:
        for path in os.environ["PATH"].split(os.pathsep):
            path = path.strip('"')
            exe_file = os.path.join(path, program)
            if is_exe(exe_file):
                return exe_file

    return None
