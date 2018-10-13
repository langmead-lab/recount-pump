#!/usr/bin/env python

# Author: Ben Langmead <ben.langmead@gmail.com>
# License: MIT

import os
import sys
import hashlib
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


def engine_from_config(fn, section='client', echo=True):
    config = RawConfigParser(allow_no_value=True)
    if not os.path.exists(fn):
        raise RuntimeError('No such ini file: "%s"' % fn)
    config.read(fn)
    engine_url = config.get(section, "url")
    return create_engine(engine_url, echo=echo)


def session_maker_from_config(fn, section='client'):
    engine = engine_from_config(fn, section=section)
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine)


def parse_queue_config(fn, section='queue'):
    cfg = RawConfigParser(allow_no_value=True)
    if not os.path.exists(fn):
        raise RuntimeError('No such ini file: "%s"' % fn)
    cfg.read(fn)

    def _get_option(nm):
        opt = cfg.get(section, nm) if cfg.has_option(section, nm) else None
        return None if (len(opt) == 0) else opt

    return _get_option('aws_profile'), _get_option('region'), _get_option('endpoint')


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
