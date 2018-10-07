#!/usr/bin/env python

# Author: Ben Langmead <ben.langmead@gmail.com>
# License: MIT

import globus_sdk


def new_transfer_client(config, section='recount-app'):
    """
    App authenticating
    """
    confidential_client = globus_sdk.ConfidentialAppAuthClient(
        client_id=config.get(section, 'id'),
        client_secret=config.get(section, 'secret'))
    scopes = "urn:globus:auth:scope:transfer.api.globus.org:all"
    cc_authorizer = globus_sdk.ClientCredentialsAuthorizer(
        confidential_client, scopes)
    return globus_sdk.TransferClient(authorizer=cc_authorizer)


def globus_activate(config, transfer_client, section, hours=1):
    """
    User authenticating to transfer endpoints
    """
    ep_id = config.get(section, 'id')
    user = config.get(section, 'username')
    password = config.get(section, 'passphrase')
    server_dn = config.get(section, 'server_dn')
    oauth_host = config.get(section, 'oauth_host')
    myproxy_host = config.get(section, 'myproxy_host')
    data = list()
    data.append({
        "type": "myproxy",
        "name": "hostname",
        "value": myproxy_host,
        "required": True,
        "private": False,
        "ui_name": "MyProxy Server",
        "description": "Hostname for MyProxy server.",
        "DATA_TYPE": "activation_requirement"})
    data.append({
        "type": "myproxy",
        "name": "username",
        "value": user,
        "required": True,
        "private": False,
        "ui_name": "Username",
        "description": "Username for MyProxy server.",
        "DATA_TYPE": "activation_requirement"})
    data.append({
        "type": "myproxy",
        "name": "passphrase",
        "value": password,
        "required": True,
        "private": True,
        "ui_name": "Passphrase",
        "description": "Passphrase for MyProxy server.",
        "DATA_TYPE": "activation_requirement"})
    if server_dn is not None and len(server_dn) > 0:
        data.append({
            "type": "myproxy",
            "name": "server_dn",
            "value": server_dn,
            "required": False,
            "private": False,
            "ui_name": "Server DN",
            "description": "Distinguished name of MyProxy server",
            "DATA_TYPE": "activation_requirement"})
    data.append({
        "type": "myproxy",
        "name": "lifetime_in_hours",
        "value": str(hours),
        "required": False,
        "private": False,
        "ui_name": "Credential Lifetime (hours)",
        "description": "Lifetime in hours",
        "DATA_TYPE": "activation_requirement"
    })
    req_doc = {
        'DATA': data,
        'DATA_TYPE': u'activation_requirements',
        'activated': False,
        'auto_activation_supported': True,
        'expire_time': None,
        'expires_in': 0,
        'length': len(data),
        'oauth_server': oauth_host}
    return transfer_client.endpoint_activate(ep_id, req_doc)
