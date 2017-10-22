#!/usr/bin/env python

import globus_sdk


def get_auth_data(client_id):
    try:
        input = raw_input
    except NameError:
        pass

    client = globus_sdk.NativeAppAuthClient(client_id)
    client.oauth2_start_flow()

    authorize_url = client.oauth2_get_authorize_url()
    print('Please go to this URL and login: {0}'.format(authorize_url))

    # this is to work on Python2 and Python3 -- you can just use raw_input() or
    # input() for your specific version
    auth_code = input(
        'Please enter the code you get after login here: ').strip()
    token_response = client.oauth2_exchange_code_for_tokens(auth_code)

    auth_data = token_response.by_resource_server['auth.globus.org']
    transfer_data = token_response.by_resource_server['transfer.api.globus.org']

    # most specifically, you want these tokens as strings
    return auth_data, transfer_data
