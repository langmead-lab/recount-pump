# recount-pump

This will give a high level overview of the process of configuring and running a specific project through the Monorail pipeline.

For details, please see the  READMEs associated with the various sub-components (e.g. projects).

Nomenclature note: "run" here is used in terms of a single project's instantiation as a Monorail pipeline.
To differentiate it from the SRA's base unit of sequencing (also called "run", e.g. identified by an [SED]RR accession), we will slightly abuse the terminology of the SRA by calling all sequencing runs "samples".  For the purposes of this document this is acceptable, though not technically true when discussing sequencing in general.

## Projects

Monorail revolves around the idea of a `project` which defines the following:

* Label/name of a run (e.g. "sra_human_v3")
* Set of sample identifiers (if SRA, this is a list of accessions)
* Monorail docker image name/version to be used for the pipeline
* Species information (e.g. name, taxon ID, reference short name [hg38])

This is stored in the `project.ini` file in the projects/<proj_name>/ subdirectory.

There is also the projects/<proj_name>/creds subdirectory which stores the project-specific settings per-module (e.g. for Globus).
These can be created in a semi-automated way, but typically once one or more projects have been defined for a group, copying and editing these files between projects is reasonable.

Additionally there are two files which define organization-wide AWS settings.

All settings related files are discussed further at the end of this README.

The set of sample identifiers, typically either a JSON or text file, is copied to the project directory on S3.
The S3 URL is then referenced in the project.ini file, e.g.:

`s3://recount-pump-experiments/sra_human_v3/tranche_0.txt.gz`

This will be used to populate the AWS RDS DB for the project with the list of sample identifiers in the "Initializing the Project Model" step.
Each sample is assigned an integer ID which is used to link it between the DB and the SQS queue.

## Initializing the Project Model



## Settings Files

### Project-specific Settings files



### Generic Settings Files

The settings below are typically set once for a organization/group and shared between multiple `projects`.

#### public_conf.ini

* Profile
* Region
* Subnets
* RDS DB port/DNS

#### private_conf.ini

* Confidential AWS RDS DB password




`ini` files:

* MySQL
    * Get credentials from BTL
    * I have two sets, one for local db used for 
    * `~/.recount/db.ini`
    * `~/.recount/local_db.ini`
testing, one for the always-on AWS one
* Logging / aggregation
    * `~/.recount/log.ini`
    * Get credentials from BTL
* Docker hub
    * `~/.docker/creds.txt`
    * Used by `vagrant/Vagrantfile`
* AWS credentials file
    * `~/.aws/credentials`
    * Need to have read access to recount-pump bucket owned by 526853323356
    * Reference files stored here
    * Used by `src/mover.py`, which in turn is used by other modules

