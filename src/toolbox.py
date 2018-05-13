#!/usr/bin/env python

# Author: Ben Langmead <ben.langmead@gmail.com>
# License: MIT

import os
import hashlib


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


def session_maker_from_config(fn):
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from base import Base
    try:
        from ConfigParser import RawConfigParser
    except ImportError:
        from configparser import RawConfigParser

    config = RawConfigParser(allow_no_value=True)
    config.readfp(fn)
    engine_url = config.get("recount", "url")
    engine = create_engine(engine_url, echo=True)
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine)


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
