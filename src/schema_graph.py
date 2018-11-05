#!/usr/bin/env python

# Author: Ben Langmead <ben.langmead@gmail.com>
# License: MIT

"""schema_graph.py

Usage:
  schema_graph plot [options]

Options:
  --prefix <path>          Write plot files beginning with <path> [default: recount].
  --db-ini <ini>           Database ini file [default: ~/.recount/db.ini].
  --db-section <section>   ini file section for database [default: client].
  --log-ini <ini>          ini file for log aggregator [default: ~/.recount/log.ini].
  --log-level <level>      set level for log aggregation; could be CRITICAL,
                           ERROR, WARNING, INFO, DEBUG [default: INFO].
  -h, --help               Show this screen.
  --version                Show version.
"""


import os
import log
import tempfile
from docopt import docopt
from toolbox import session_maker_from_config
from sqlalchemy import MetaData
from sqlalchemy_schemadisplay import create_schema_graph


def make_graphs(prefix, session):
    graph = create_schema_graph(
        metadata=MetaData(session.get_bind()),
        show_datatypes=False,  # The image would get nasty big if we'd show the datatypes
        show_indexes=False,    # ditto for indexes
        rankdir='LR',          # From left to right (instead of top to bottom)
        concentrate=False)     # Don't try to join the relation lines together

    graph.write_png('%s_dbschema.png' % prefix)
    graph.write_svg('%s_dbschema.svg' % prefix)
    graph.write_pdf('%s_dbschema.pdf' % prefix)


def test_make_graphs(session):
    tmpdir = tempfile.mkdtemp()
    prefix = os.path.join(tmpdir, 'test')
    make_graphs(prefix, session)
    assert os.path.exists(prefix + '_dbschema.png')


if __name__ == '__main__':
    args = docopt(__doc__)
    log_ini = os.path.expanduser(args['--log-ini'])
    log.init_logger(log.LOG_GROUP_NAME, log_ini=log_ini, agg_level=args['--log-level'])
    # sqlalchemy is way too verbose here so nix it
    #log.init_logger('sqlalchemy', log_ini=log_ini, agg_level=args['--log-level'],
    #                sender='sqlalchemy')
    try:
        if args['plot']:
            db_ini = os.path.expanduser(args['--db-ini'])
            Session = session_maker_from_config(db_ini, args['--db-section'])
            #url = url_from_db_ini(db_ini, section=args['--db-section'])
            print(make_graphs(args['--prefix'], Session()))
    except Exception:
        log.error('Uncaught exception:', 'schema_graph.py')
        raise
