# recount-pump

This will give a high level overview of the process of configuring and running a specific project through the Monorail pipeline.

For details, please see the  READMEs associated with the various sub-components (e.g. projects).

Nomenclature note: "run" here is used in terms of a single project's instantiation as a Monorail pipeline.
To differentiate it from the SRA's base unit of sequencing (also called "run", e.g. identified by an [SED]RR accession), we will slightly abuse the terminology of the SRA by calling all sequencing runs "samples".  For the purposes of this document this is acceptable, though not technically true when discussing sequencing in general.

## Projects

A working project which also serves as a good example is here:
https://github.com/langmead-lab/recount-pump/tree/master/projects/tcga

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

## Cluster Configuration

There are a group of settings files which control how Monorail interacts with the AWS modules (SQS, RDS, Watchtower/CloudWatch) and with Globus, partial examples of these are here:

https://github.com/langmead-lab/recount-pump/tree/master/projects/common/creds

Typically, Monorail is run in an HPC environment using Singularity to abstract ease the pain of dependency management.
Monorail *can* be run outside of containers ("bare metal") but this is not recommended for most cases and is not covered here.

The key settings file for cluster configuration is the `cluster.ini` file, detailed at the end of this README.

An partial example is here:

https://github.com/langmead-lab/recount-pump/blob/master/projects/common/clusters/marcc/public_conf.ini

This file also serves as a reference point for which path temporary/output files will be deposited during a run (useful for debugging).

## Initializing the Project Model

Once all settings files have been configured, the project needs to be initialized.

The following scripts should be run from within the project working directory (typically `projects/<proj_name>`).

`projects/common/init_model.sh`
and
`projects/common/reset.sh`

The `init_model.sh` script will perform the following actions:

* Creation of AWS RDS DB
* Population of AWS RDS DB with sample IDs and reference/annotation data set
* Add Monorail Docker image name/version to database
* Creation of AWS SQS Queue
* Stage sample IDs as messages in SQS queue

This information represents the main "state" of the project/run.  

If there is a problem in the initialization or later in the project run that relates to configuration, it's usually best to start fresh with a new initialization run.

This can be done by resetting the project in AWS (DB/SQS) with the `reset.sh` script listed above.

### Worker Run Configuration

Once the project has been initialized, Monorail can be run.
This section assumes you're running on a local HPC cluster, but it could be extended to include remote resources on AWS or equivalent.

There are 3 types of entities important in this section:

* Jobs

A job is an attempt at processing a single sample through Monorail (it could fail)

* Workers

A worker is the atomic agent of Monorail, it represents a single python process which instantiates a container for each new job, which in turn runs a Snakemake pipeline within the container.  A worker will continue to run as long as 1) there are jobs on the SQS queue and 2) the queue is accessible.

* Nodes

Each node represents a machine (or VM) allocated, in part or in whole, to Monorail to run one or more workers to process jobs.  Each allocation of a node will start a parent python process which will then spawn one or more child python worker processes.  

To start Monorail running on a node, typically, a batch script is submitted to the HPC's scheduler (e.g. Slurm) to request a lease of a node.

This script will typically set the following:

* HPC scheduler partition/queue to lease from
* Name of lease
* Time requested (e.g. 12 hours)
* Hardware resources requested (e.g. 12 cores, 90G memory)
* Account to charge lease to (if applicable)
* List of nodes to exclude (blacklising, if applicable)

An example is the Slurm node settings for the TACC (XSEDE) Stampede2 cluster using Skylake Xeons (SKX):
https://github.com/langmead-lab/recount-pump/blob/master/projects/common/clusters/stampede2/skx-normal/partition.ini
MARCC (Slurm):
https://github.com/langmead-lab/recount-pump/blob/master/projects/common/clusters/marcc/parallel/partition.ini

In addition it will setup the environment to start the Monorail parent process on that node, which includes loading the Singularity module.
And finally it will start the `cluster.py` parent python process with parameters which point to the various `.ini` files.

## Victory Conditions

Nodes will stop processing for one of 3 reasons:

* The time limit on the node lease ends
* The job queue is exhausted
* A runtime error causes the parent python process running on the node to prematurely terminate

By far the most common cause for node stopages is the first one, since node lease time limits tend to be much shorter than what's needed to process a medium-large Monorail run.  This will have the effect of stopping jobs in the middle which will need to be restarted.  This is expected and these jobs will be visible again on the queue after a pre-defined time period (typically 30 min-3 hours) controlled by `visibility_timeout` in the `creds/queue.ini` settings file for the project.

If many concurrent attempts are made which end up being successful for a particular job, this indicates the `visibility_timeout` setting for the job queue is too short and should be elongated.

Also related to this, the `max_receive_count` also in `creds/queue.ini`, controls how many times a job is attempted before dumping it to the Dead Letter Queue (DLQ).  Typically this is 3-6 times, depending on the project, however, in certain cases (SRA) it may be necessary to reduce this to 1 to rapidly fail samples which simply won't download.

In the 2nd case above, the parent process running on the node will wait until all worker children have finished w/o error and then it will finish itself and relinquish the node.  If a worker process fails for any reason, the parent will start a new process in its place and  continue checking children processes. 


## Settings Files

### Project-specific Settings files

#### cluster.ini

This file defines the following:

* Cluster name
* Container system (typically "Singularity")
* Path to Singularity image file
* Input path
* Output path
* Temp path
* Reference file set path
* \# of workers (`workers`)
* \# of cores per worker (`cpus`)

Paths are always absolute.
Input/output/temp paths are defined both for the host OS *and* for the container.
The container paths are where the host OS paths are mounted in the container, so they reference the same thing.

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

