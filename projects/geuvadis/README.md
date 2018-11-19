## `recount-pump` GEUVADIS experiment

* `../../aws/db/create_db.sh recount`
* `get_hg38_parts.sh`
    * Downloads components of the hg38 reference from synapse to current directory
        * HISAT2 index
        * FASTA
        * GTF (GENCODE)
* `upload_hg38_parts.sh`
    * Uploads components of the hg38 reference to the expected spot in S3: `s3://recount-ref/hg38`
* `get_meta.sh`
    * Get the metadata for the samples in question
* `upload_meta.sh`
    * Upload the `.json.gz` file produced by the previous script to S3 for safe & permanent keeping
* `init_model.sh`
    * Sets up the data model and stages the project
        * Sources
        * Analysis
        * Reference
        * Inputs/InputSet
    * But stops after staging; no actual jobs are started

### Steps on a cluster

* Set up `ini` files
    * `db_aws.ini`: database-related settings, modeled on `ini/db.ini` under this directory
    * `s3_aws.ini`: settings for connecting to S3 on AWS, modeled on `ini/s3.ini`
    * `cluster-skx.ini`: cluster details like which container system to use and which directories to use for inputs, outputs, etc.  This one is for Stampede 2 Skylake, hence the `-skx` in the name.
    * `dest_geuvadis.ini`: where to copy results files
    * `queue_aws.ini`: AWS settings for queue
    
These are usually all created in the `$HOME/.recount` subdirectory.  Below I will refer to them as though they are there.

Once these have been created and customized, the following command ensures that the cluster has the reference and analysis image files at the ready.  It's assumed that the directories where these files are being stored (`analysis_dir` and `ref_base` from `cluster.ini`) are on shared filesystems, so that jobs submitted to the cluster can see them too.

* `python cluster.py prepare --ini-base $WORK/git/recount-pump/projects/geuvadis/creds --cluster-ini ~/.recount/cluster-skx.ini 1`
* `rm -rf $(grep '^input_base' ~/.recount/cluster-skx.ini | cut -f 3 -d' ')/*`
* `rm -rf $(grep '^output_base' ~/.recount/cluster-skx.ini | cut -f 3 -d' ')/*`
* `rm -rf $(grep '^temp_base' ~/.recount/cluster-skx.ini | cut -f 3 -d' ')/*`
* `python cluster.py run --ini-base $WORK/git/recount-pump/projects/geuvadis/creds --cluster-ini ~/.recount/cluster-skx.ini 1`

### Monitoring/studying the run

Thanks to log aggregation, you can go back and get a very complete picture of what happened during the run.  This directory includes some scripts to help with this:

* `get_logs.sh`
    * Get logs from the log stream we created with `create_log_stream.sh`

Dump the database to S3 when it's done?

### Notes on how a user would do this

The instructions above are for someone looking to include the results in the official recount resource.

* First two steps (downloading then uploading the components of the h38 reference) will already be done and user will just have to download a bundle to their cluster first.