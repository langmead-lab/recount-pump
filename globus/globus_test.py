#!/usr/bin/env python

from __future__ import print_function
from globus_access import get_auth_data
from globus_endpoints import marcc_dtn, xsede_s2, bens_mbp
import globus_sdk

if __name__ == '__main__':
    # Copied from here: https://auth.globus.org/v2/web/developers
    # After following directions here: http://globus-sdk-python.readthedocs.io/en/stable/tutorial/
    # "It's non-secure information and you can treat it as such"
    client_id = open('client_id.txt').read().strip()

    auth_data, transfer_data = get_auth_data(client_id)

    authorizer = globus_sdk.AccessTokenAuthorizer(transfer_data['access_token'])
    tc = globus_sdk.TransferClient(authorizer=authorizer)

    # high level interface; provides iterators for list responses

    print('Printing MARCC directory:')
    for entry in tc.operation_ls(marcc_dtn['id'], path="/scratch/groups/blangme2/rail_data/geuvadis/data"):
        print(entry["name"], entry["type"])

    print('Printing Stampede directory:')
    for entry in tc.operation_ls(xsede_s2['id'], path="/~/"):
        print(entry["name"], entry["type"])

    print('Printing MBP directory:')
    for entry in tc.operation_ls(bens_mbp['id'], path="/Users/langmead/tmp/"):
        print(entry["name"], entry["type"])

    # do a dummy transfer
    tdata = globus_sdk.TransferData(
        tc,
        marcc_dtn['id'],
        bens_mbp['id'],
        label = "SDK example",
        sync_level = "checksum")
    tdata.add_item("/scratch/groups/blangme2/rail_data/geuvadis/data/ERR188471_1.fastq.gz", "/Users/langmead/tmp/ERR188471_1.fastq.gz")
    transfer_result = tc.submit_transfer(tdata)
