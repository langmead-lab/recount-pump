This is a small test project.  This is the project we use to test the overall pump workflow in integration and end-to-end tests.

Some things to note about the config files:

* We need a set of cluster-level config files that describe the integration test setup
    * These are in `projects/common/clusters/integration`
    * These are designed to work onF the Vagrant systems described in the `vagrant/recount-dev` and `vagrant/build_integration` directories
* The analysis URL refers to a locally registered Docker image; doesn't use a public repo
* In the integration testing setting, there is a minio container running that emulates S3
    * This allows us to have the metadata live at an S3 URL: `s3://recount-meta/ce10_test/ce10_small_test.json.gz`
    * Postgres container is also running, allowing us to connect to db at `localhost:25432`
    * ElasticMQ is running, allowing us to connect to SQS like service at `http://localhost:29324`
* We use minio's client (`mc`) to interact with S3 in our scripts here
    * This requires that we install a config file

To prepare for the test:

```sh
export RECOUNT_INTEGRATION_TEST=1
./setup.sh && ../common/make_creds.py
docker image ls -q quay.io/benlangmead/recount-rs5:latest
```

The last command should print a hex string.

And ensure that a Docker image for `docker://recount-rs5:latest`

To run the test:

```sh
export RECOUNT_INTEGRATION_TEST=1
./check_buckets.sh && ../common/init_model.sh && ./run.sh
```
