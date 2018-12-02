#!/usr/bin/env python

# Author: Ben Langmead <ben.langmead@gmail.com>
# License: MIT

"""meta

Usage:
  meta load-json <file> <table> [options]

Options:
  <file>                   JSON file to load.
  <table>                  Table name to install in db.
  --db-ini <ini>           Database ini file [default: ~/.recount/db.ini].
  --db-section <section>   ini file section for database [default: client].
  --log-ini <ini>          ini file for log aggregator [default: ~/.recount/log.ini].
  --log-level <level>      Set level for log aggregation; could be CRITICAL,
                           ERROR, WARNING, INFO, DEBUG [default: INFO].
  --ini-base <path>        Modify default base path for ini files.
  --overwrite              Overwrite table if one of same name exists.
  -h, --help               Show this screen.
  --version                Show version.
"""

import os
import pandas
import log
import json
from docopt import docopt
from pandas.io.json import json_normalize
from toolbox import session_maker_from_config
from sqlalchemy.types import JSON


def import_from_json(json_fn, table_name, session, overwrite=False):
    with open(json_fn, 'r') as fh:
        df = json_normalize(json.load(fh))
        dtype_dict = {}
        colname_dict = {}
        for colname in df:
            new_colname = colname
            if colname.startswith('_source.'):
                new_colname = colname[8:]
                colname_dict[colname] = new_colname
            if 'date' in colname or 'Date' in colname:
                print((colname, df[colname].dtype))
                df[colname] = pandas.to_datetime(df[colname] / 1000, unit='s')
            print((colname, df[colname].dtype))
            if '_identifiers' in colname or '_attributes' in colname or \
                    '_xrefs' in colname or colname == '_source.run.reads' or \
                    colname == '_source.run.file_addons':
                dtype_dict[new_colname] = JSON
        df = df.rename(index=str, columns=colname_dict)
        ife = 'replace' if overwrite else 'fail'
        df = df.drop(['_id', '_index', '_score', '_type'], axis=1)
        df.to_sql(table_name, session.connection(), if_exists=ife, dtype=dtype_dict)
        session.commit()


def go():
    args = docopt(__doc__)

    def ini_path(argname):
        path = args[argname]
        if path.startswith('~/.recount/') and args['--ini-base'] is not None:
            path = os.path.join(args['--ini-base'], path[len('~/.recount/'):])
        return os.path.expanduser(path)

    log_ini = ini_path('--log-ini')
    log.init_logger(log.LOG_GROUP_NAME, log_ini=log_ini, agg_level=args['--log-level'])
    try:
        log.info('In main', 'meta.py')
        db_ini = ini_path('--db-ini')
        if args['load-json']:
            session_mk = session_maker_from_config(db_ini, args['--db-section'])
            import_from_json(args['<file>'], args['<table>'], session_mk(), overwrite=args['--overwrite'])
    except Exception:
        log.error('Uncaught exception:', 'meta.py')
        raise


if __name__ == '__main__':
    go()
