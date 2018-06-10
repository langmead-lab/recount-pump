# recount-pump

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

