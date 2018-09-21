#!/usr/bin/env python

import json
import globus_sdk


def new_transfer_client(config, section='recount-app'):
    confidential_client = globus_sdk.ConfidentialAppAuthClient(
        client_id=config.get(section, 'id'),
        client_secret=config.get(section, 'secret'))
    scopes = "urn:globus:auth:scope:transfer.api.globus.org:all"
    cc_authorizer = globus_sdk.ClientCredentialsAuthorizer(
        confidential_client, scopes)
    return globus_sdk.TransferClient(authorizer=cc_authorizer)


def activate_xsede(config, transfer_client):
    xsede_ep_id = config.get('globus-xsede', 'id')
    xsede_user = config.get('globus-xsede', 'username')
    xsede_password = config.get('globus-xsede', 'password')
    reqs_doc = transfer_client.endpoint_get_activation_requirements(xsede_ep_id)
    reqs_json = json.loads(str(reqs_doc))
    assert reqs_json['DATA'][3]['name'] == 'username'
    assert reqs_json['DATA'][4]['name'] == 'passphrase'
    reqs_json['DATA'][3]['value'] = xsede_user
    reqs_json['DATA'][4]['value'] = xsede_password
    return transfer_client.endpoint_activate(xsede_ep_id, reqs_json)


def activate_marcc(config, transfer_client, hours=1):
    marcc_ep_id = config.get('globus-marcc', 'id')
    marcc_user = config.get('globus-marcc', 'username')
    marcc_password = config.get('globus-marcc', 'passphrase')
    marcc_dn = config.get('globus-marcc', 'server_dn')
    marcc_oauth_host = config.get('globus-marcc', 'oauth_host')
    req_doc = {'DATA': [
        {
            "type": "myproxy",
            "name": "hostname",
            "value": marcc_oauth_host,
            "required": True,
            "private": False,
            "ui_name": "MyProxy Server",
            "description": "The hostname of the MyProxy server to request a credential from.",
            "DATA_TYPE": "activation_requirement"
        },
        {
            "type": "myproxy",
            "name": "username",
            "value": marcc_user,
            "required": True,
            "private": False,
            "ui_name": "Username",
            "description": "The username to use when connecting to the MyProxy serever.",
            "DATA_TYPE": "activation_requirement"
        },
        {
            "type": "myproxy",
            "name": "passphrase",
            "value": marcc_password,
            "required": True,
            "private": True,
            "ui_name": "Passphrase",
            "description": "The passphrase to use when connecting to the MyProxy serever.",
            "DATA_TYPE": "activation_requirement"
        },
        {
            "type": "myproxy",
            "name": "server_dn",
            "value": marcc_dn,
            "required": False,
            "private": False,
            "ui_name": "Server DN",
            "description": "The distinguished name of the MyProxy server, formated with '/' as the separator. This is only needed if the server uses a non-standard certificate and the hostname does not match.",
            "DATA_TYPE": "activation_requirement"
        },
        {
            "type": "myproxy",
            "name": str(hours),
            "value": "1",
            "required": False,
            "private": False,
            "ui_name": "Credential Lifetime (hours)",
            "description": "The lifetime for the credential to request from the server, in hours. Depending on the MyProxy server's configuration, this may not be respected if it's too high. If no lifetime is submitted, the value configured as the default on the  server will be used.",
            "DATA_TYPE": "activation_requirement"
        }],
        'DATA_TYPE': u'activation_requirements',
        'activated': False,
        'auto_activation_supported': True,
        'expire_time': None,
        'expires_in': 0,
        'length': 2,
        'oauth_server': marcc_oauth_host}
    return transfer_client.endpoint_activate(marcc_ep_id, req_doc)