#!/usr/bin/env python

from __future__ import print_function
import os
import globus_recount
import globus_sdk
import logging

try:
    from ConfigParser import RawConfigParser
except ImportError:
    from configparser import RawConfigParser


def globus_config():
    fn = os.path.expanduser('~/.recount/globus.ini')
    config = RawConfigParser(allow_no_value=True)
    if not os.path.exists(fn):
        raise RuntimeError('No such ini file: "%s"' % fn)
    config.read(fn)
    return config


def go():
    logging.basicConfig(level=logging.INFO)
    config = globus_config()
    tc = globus_recount.new_transfer_client(config)

    logging.info('Deactivating XSEDE')
    tc.endpoint_deactivate(config.get('globus-xsede', 'id'))
    logging.info('Deactivating MARCC')
    tc.endpoint_deactivate(config.get('globus-marcc', 'id'))

    logging.info('Activating XSEDE')
    resp = globus_recount.globus_activate(config, tc, 'globus-xsede')
    assert resp['message'].startswith('Endpoint activated success')
    logging.info('Response: ' + resp['message'])
    logging.info('Activating MARCC')
    resp = globus_recount.globus_activate(config, tc, 'globus-marcc')
    assert resp['message'].startswith('Endpoint activated success')
    logging.info('Response: ' + resp['message'])

    # do a dummy transfer
    tdata = globus_sdk.TransferData(
        tc,
        config.get('globus-xsede', 'id'),
        config.get('globus-marcc', 'id'),
        label="SDK example",
        sync_level="checksum")
    tdata.add_item("/work/04265/benbo81/stampede2/test.txt",
                   "/net/langmead-bigmem-ib.bluecrab.cluster/storage/recount-pump/test2.txt")

    logging.info('Submitting transfer task')
    transfer_result = tc.submit_transfer(tdata)

    logging.info('Waiting for task completion')
    success = tc.task_wait(transfer_result['task_id'], timeout=60)
    if not success:
        raise RuntimeError('Error waiting for task')

    logging.info('Finished!')
    print(transfer_result)


if __name__ == '__main__':
    go()
