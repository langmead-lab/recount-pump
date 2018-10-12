## `recount-pump` GEUVADIS experiment

### `ini` files

* `log.ini`
    * We want all log messages aggregated in a single log stream, maybe dedicated just to this project
* `destination.ini`
    * We want the output files to ultimately go to MARCC

### Steps to run

Get a database up and running?

Create a queue?

* `get_hg38_parts.sh`
    * Downloads components of the hg38 reference from synapse to current directory
        * HISAT2 index
        * FASTA
        * GTF (GENCODE)
* `upload_hg38_parts.sh`
    * Uploads components of the hg38 reference to the expected spot in S3: `s3://recount-pump/ref/hg38`
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
* `create_log_stream.sh`
    * XYZ

At this point, there 

* Setting up `ini` files
    * We want to 

### Monitoring/studying the run

Thanks to log aggregation, you can go back and get a very complete picture of what happened during the run.  This directory includes some scripts to help with this:

* `get_logs.sh`
    * Get logs from the log stream we created with `create_log_stream.sh`

Dump the database to S3 when it's done?

### Notes on how a user would do this

The instructions above are for someone looking to include the results in the official recount resource.

* First two steps (downloading then uploading the components of the h38 reference) will already be done and user will just have to download a bundle to their cluster first.