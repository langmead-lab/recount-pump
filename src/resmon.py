#!/usr/bin/python

"""resmon

Usage:
  resmon [options] collect <seconds> <interval>

Options:
  <seconds>                Number of seconds to collect before exiting
  <interval>               Seconds of interval between collections
  --log-ini <ini>          ini file for log aggregator [default: ~/.recount/log.ini].
  --log-section <section>  ini file section for log aggregator [default: log].
  --log-level <level>      set level for log aggregation; could be CRITICAL,
                           ERROR, WARNING, INFO, DEBUG [default: INFO].
  -a, --aggregate          enable log aggregation.
  -h, --help               Show this screen.
  --version                Show version.
"""

"""
resmon.py

Resource monitor monitors system wide resource usage and availability. This
script assumes that the number of CPU cores does not change throughout the
course.

NIC monitor component monitors the speed, in terms of Bps and Pkts/sec, and
error and drop counts, of the specified NICs.

Process monitor component monitors resource usage of of a subset of living
processes.  For example, if keyword "docker" is given, then it reports, every
T seconds, the sum of resource (CPU, RSS, IO, CtxSw, NThreads) usage of all
processes whose name contains "docker" and their child processes.

@author
Xiangyu Bu <bu1@purdue.edu>

https://github.com/xybu/python-resmon/blob/master/resmon/resmon.py

!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
Adapted for use in recount-pump
Ben Langmead
6/9/2018
!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
"""

import psutil
import time
import log
import os
from docopt import docopt
from threading import Thread


class SysmonThread(Thread):

    def __init__(self, seconds=10):
        Thread.__init__(self)
        ncores = self.ncores = psutil.cpu_count()
        msg = 'Timestamp,  Uptime, NCPU, %CPU, ' + ', '.join(['%CPU' + str(i) for i in range(ncores)]) + \
              ', %MEM, mem.total.KB, mem.used.KB, mem.avail.KB, mem.free.KB' + \
              ', %SWAP, swap.total.KB, swap.used.KB, swap.free.KB' + \
              ', io.read, io.write, io.read.KB, io.write.KB, io.read.ms, io.write.ms'
        log.info(__name__, msg, 'resmon.py')
        self.prev_disk_stat = psutil.disk_io_counters()
        self.starttime = int(time.time())
        self.closed = False
        self.seconds = seconds

    def close(self):
        self.closed = True
 
    def run(self):
        while not self.closed:
            self.poll_stat()
            time.sleep(self.seconds)

    def poll_stat(self):
        timestamp = int(time.time())
        uptime = timestamp - self.starttime
        total_cpu_percent = psutil.cpu_percent(percpu=False)
        percpu_percent = psutil.cpu_percent(percpu=True)
        mem_stat = psutil.virtual_memory()
        swap_stat = psutil.swap_memory()
        disk_stat = psutil.disk_io_counters()

        line = str(timestamp) + ', ' + str(uptime) + ', ' + \
            str(self.ncores) + ', ' + str(total_cpu_percent*self.ncores) + ', '
        line += ', '.join([str(i) for i in percpu_percent])
        line += ', ' + str(mem_stat.percent) + ', ' + str(mem_stat.total >> 10) + ', ' + str(
            mem_stat.used >> 10) + ', ' + str(mem_stat.available >> 10) + ', ' + str(mem_stat.free >> 10)
        line += ', ' + str(swap_stat.percent) + ', ' + str(swap_stat.total >> 10) + \
            ', ' + str(swap_stat.used >> 10) + ', ' + str(swap_stat.free >> 10)
        line += ', ' + str(disk_stat.read_count - self.prev_disk_stat.read_count) + \
                ', ' + str(disk_stat.write_count - self.prev_disk_stat.write_count) + \
                ', ' + str((disk_stat.read_bytes - self.prev_disk_stat.read_bytes) >> 10) + \
                ', ' + str((disk_stat.write_bytes - self.prev_disk_stat.write_bytes) >> 10) + \
                ', ' + str(disk_stat.read_time - self.prev_disk_stat.read_time) + \
                ', ' + str(disk_stat.write_time - self.prev_disk_stat.write_time)

        log.info(__name__, line, 'resmon.py')
        self.prev_disk_stat = disk_stat


def collect(seconds, interval):
    sm = SysmonThread(seconds=int(interval))
    sm.start()
    time.sleep(int(seconds))
    log.info(__name__, 'Closing monitor thread', 'resmon.py')
    sm.close()
    log.info(__name__, 'Joining monitor thread', 'resmon.py')
    sm.join()


if __name__ == '__main__':
    args = docopt(__doc__)
    agg_ini = os.path.expanduser(args['--log-ini']) if args['--aggregate'] else None
    log.init_logger(__name__, log_ini=agg_ini, agg_level=args['--log-level'])
    try:
        if args['collect']:
            collect(args['<seconds>'], args['<interval>'])
    except Exception:
        log.error(__name__, 'Uncaught exception:', 'resmon.py')
        raise
