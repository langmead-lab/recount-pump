## Minio

This directory contains scripts to build, push, and run a [Minio](https://www.minio.io) container.  Minio emulates the S3 API.  The image has pre-installed data that can drive end-to-end tests using the C elegans genome.  Pre-installed files include:

* Metadata from SRAdbV2 in the form of a compressed JSON file as compiled by `recount-pump/src/metadata/sradbv2.py`.
* Files relevant to the C elegans reference and obtained from iGenomes, including a HISAT2 Index (TODO), FASTA files, and gene annotation.
* Singularity container for the pipeline to run on each accession. (TODO)

### Steps

Many of these require `docker`.  They may also require `sudo` for the docker commands, depending on your system.

* `manifest.csv` -- two-column CSV file.  First column are source URLs for files to be included in the image.  Second column are corresponding destination buckets & paths.
* `build.sh` -- build a minio image with the files from `manifest.csv` pre-installed at the expected places.  Also installs the `recount-pump` code and uses it to download metadata and save to a JSON file.
    * Though it's not generally a good idea to copy files into the current directory just before building the Docker image, we do that here because it's a convenient way to get the `recount-pump` code into the image.  Once the repo is public, it could be cloned instead.  Alternately, maybe Docker secrets can be used to allow the container to borrow a private key to clone the private repo. 
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
