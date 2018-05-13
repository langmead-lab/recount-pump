#!/usr/bin/env python

# Author: Ben Langmead <ben.langmead@gmail.com>
# License: MIT

"""
Uses a --defailts-file, which is an ini file, to store information about host,
user, port, password.  The thought is that this is somewhat more secure than
supplying these on the command line.  The variables should be in the [client]
section, like this:

[client]
password=XXX
host=db-name.long-id.us-east-1.rds.amazonaws.com
port=3306
user=me

Don't include a database=<XYZ> variable.  mysqladmin doesn't like this.

Helpful command for debugging what defaults mysql will get:
mysql --defaults-file=XYZ--print-defaults
"""

from __future__ import print_function
import os
import sys
import tempfile
from toolbox import which


ini_dir = os.path.expanduser('~/.recount')
ini_fn = os.path.join(ini_dir, 'db.ini')


def sql_command():
    sql = which('mysql')
    if sql is None:
        raise RuntimeError('mysql must be installed and in PATH')
    return sql


def sqladmin_command():
    sql = which('mysqladmin')
    if sql is None:
        raise RuntimeError('mysqladmin must be installed and in PATH')
    return sql


def admin_status():
    cmd = [sqladmin_command(), '--defaults-file=' + ini_fn, 'status']
    cmd = ' '.join(cmd)
    print(cmd, file=sys.stderr)
    os.system(cmd)


def table_summary(database='recount_test'):
    cmd = [sql_command(), '--defaults-file=' + ini_fn, '-D', database, '-e', '"show table status;"']
    cmd = ' '.join(cmd)
    print(cmd, file=sys.stderr)
    os.system(cmd)


def send_sql(sql, database='recount_test'):
    fh = tempfile.NamedTemporaryFile(delete=False)
    fh.write(sql)
    fh.close()
    cmd = [sql_command(), '--defaults-file=' + ini_fn, '-D', database, '<', fh.name]
    cmd = ' '.join(cmd)
    print(cmd, file=sys.stderr)
    os.system(cmd)
    os.remove(fh.name)


if __name__ == '__main__':
    admin_status()
    table_summary()
