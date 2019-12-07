import sys
import globus_sdk
import time

client_id=sys.argv[1]
client_secret=sys.argv[2]

confidential_client = globus_sdk.ConfidentialAppAuthClient(client_id=client_id, client_secret=client_secret)
scopes = "urn:globus:auth:scope:transfer.api.globus.org:all"
cc_authorizer = globus_sdk.ClientCredentialsAuthorizer(confidential_client, scopes)
tc = globus_sdk.TransferClient(authorizer=cc_authorizer)

sys.stdout.write("logged in\n")
i=0
tl=tc.task_list(num_results=None, filter="status:ACTIVE,INACTIVE")
for t in tl:
    try:
        tc.cancel_task(t['task_id'])
        #pass
    except globus_sdk.exc.TransferAPIError as te:
        time.sleep(1) 
        continue
    sys.stdout.write("canceled task %s\n" % (str(t['task_id'])))
    i+=1
sys.stdout.write("canceled %d tasks\n" % i)
