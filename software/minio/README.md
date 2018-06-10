It's easy to install a local [Minio](https://www.minio.io) server using Docker.  It also helps with performing local testing of some of `recount-pump`'s functionality.  It essentially emulates S3.  Scripts in this directory help with the process of setting up and testing a Minio server.  It's assumed you have Docker.  Note that you may have to prepend `sudo` to docker commands.

### Steps

* `pull.sh` -- pull the appropriate minio Docker image.
* `run.sh` -- run a Docker container using the image, mapping the appropriate ports on localhost to the same inside the image.
* `credentials`, `config` -- to use the AWS CLI with the local Minio server, you'll need to create a profile (called `minio`) with appropriate credentials
* `test.sh` -- run a few simple tests using the AWS CLI
* `test.py` -- run a few simple tests using Python & `boto3`

### Notes

As you can see in `test.sh`, using the AWS cli to interact with minio requires that the endpoint be specified using `--endpoint-url http://127.0.0.1:9000`.  As of now, it does not look like this can be specified once and for all in the AWS CLI configuration files.  You just have to re-specify it for each `aws s3` command.

In `test.py`, you can see that it can be specified once when creating the S3 `resource` object:

```python
import boto3
session = boto3.Session(profile_name='minio')
s3 = session.resource('s3', endpoint_url='http://127.0.0.1:9000')
``` 
