It's easy to install a local [Minio](https://www.minio.io) server using Docker.  It also helps with performing local testing of some of `recount-pump`'s functionality.  It essentially emulates S3.  Scripts in this directory help with the process of setting up and testing a Minio server with some files pre-installed in a bucket.  It's assumed you have Docker.  Note that you may have to prepend `sudo` to docker commands.

### Steps

* `manifest.csv` -- two-column CSV file.  First column are source URLs for files to be included in the image.  Second column are corresponding destination buckets & paths.
* `build.sh` -- build a minio image with the files from `manifest.csv` pre-installed at the expected places.
* `init_db.sh` -- runs as part of the `docker build` process; downloads all the files from `mainfest.csv` to a staging area
* `run.sh` -- run a Docker container using the image, mapping the appropriate ports on localhost to the same inside the image.  Needs to perform one last step (a `mv`) to ensure the files from `manifest.csv` appear as expected
* `credentials`, `config` -- to use the AWS CLI with the local Minio server, you'll need to create a profile (called `minio`) with appropriate credentials
* `test.sh` -- run a few simple tests using the AWS CLI
* `test.py` -- run a few simple tests using Python & `boto3`
* `kill.sh` -- kill the container if it's running
* `wait-for-it.sh` -- utility used to check if service is up and running on a port

### Notes

As you can see in `test.sh`, using the AWS cli to interact with minio requires that the endpoint be specified using `--endpoint-url http://127.0.0.1:9000`.  As of now, it does not look like this can be specified once and for all in the AWS CLI configuration files.  You just have to re-specify it for each `aws s3` command.

In `test.py`, you can see that it can be specified once when creating the S3 `resource` object:

```python
import boto3
session = boto3.Session(profile_name='minio')
s3 = session.resource('s3', endpoint_url='http://127.0.0.1:9000')
``` 
