### Adding a new cluster

See `common/clusters/README.md`

### Adding a new project

Pretend name is `proj1`.  Start in `projects` subdir.

* If necessary, push Docker image for analysis to quay.io
    * Make note of quay.io URL and label
* `mkdir proj1`
* Make `project.ini`

Template:

```
ana_url=docker://quay.io/benlangmead/recount-rs5:0.4.9
ana_name=rs5-049
species_short=hg38
species_long=homo_sapiens
taxid=9606
study=geuv_sc
input_json_url=s3://recount-pump-experiments/geuv_sc/geuv_sc.json.gz
```

* Create metadata file and upload it to a public URL
    * Note: if you decide to upload the metadata to our canonical `recount-pump-experiments` bucket, you will need an account under the Langmead lab JHU-based AWS account.  You will also need to have this account added to your `config` and `credentials` files.  Call it `jhu-langmead` for maximum compatibility with the scripts in `projects/common`.
    * If you are analyzing all the files in a study, follow these steps:
        1. Add a line setting the `srp` variable in `project.ini`, e.g. `srp=ERP001942`
        2. Run `../common/get_meta.sh`.  This creates a gzipped JSON file in the current directory containing all the relevant metadata
        3. Upload it so that it is available at the URL in the `input_json_url` variable in `project.ini`.  Possibly using `../common/upload_meta.sh`.
    * If the accessions are not in SRA to begin with:
        1. Create a two-column, space-separated `.txt` file with the study name in the first column and run accession in the second.  Name it `<study>.txt` where `<study>` matches the `study` variable in `project.ini`
        2. Upload it so that it is available at the URL in the `input_txt_url` variable in `project.ini`.  Possibly using `../common/upload_meta.sh`.
        3. And if there is a good source of metadata for these samples, now would be a good time to download it, and upload it to the same directory as the `.txt` file for posterity
    * For supporting projects with files either available straight through URLs (not SRA) or local to the processing cluster using the following extended format of the file above:
         1. Create a four-column, space-separated `.txt` file with the study/project name in the first column, run/sample name/id in the second, the type of access ("sra", "gdc", "url", or "local") in the third, and the ";" delimited list of URLs (if "url") or container specific paths (if "local") in the fourth.  Then follow steps 2 & 3 in the previous section.  An example of this format for a paired sample is:
         
         ```project1 sample1 local /container-mounts/recount/ref/fastqs/project1_sample1_R1.fq.gz;/container-mounts/recount/ref/fastqs/project1_sample1_R2.fq.gz```
         
The sample FASTQ files in the previous example are found under the recount reference path (defined by the variable `ref_base` for the host filesystem and `ref_mount` for the container) so that they are mounted within the container-visible filesystem.


* Make `public_conf.ini`

Template:

```
# not-very-sensitive 
db_user=recount
db_region=us-east-2
db_subnet1=subnet-03dc5fea763057c7d
db_subnet2=subnet-00dfc143f116a42aa
db_dns=recount.ceuqgjvllfuy.us-east-2
db_port=25432
db_profile=jhu-langmead

log_profile=jhu-langmead
log_region=us-east-2

sqs_profile=jhu-langmead
sqs_region=us-east-2
sqs_endpoint=

s3_profile=jhu-langmead
s3_endpoint=
```

* Make `private_conf.ini`

Template:

``` 
db_pw=<secret-password>
```

* `../common/make_creds.py`
    * Unless you happen to be running from one of the clusters that `projects/common/clusters/cluster.sh` is able to detect, this should run to completion.
* `../common/init_model.sh`
