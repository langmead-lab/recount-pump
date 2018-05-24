It's easy to install a local MySQL server using Docker.  It also helps with performing local testing of some of `recount-pump`'s functionality.  Scripts in this directory help with this process.  It's assumed you have Docker running.  Note that you may have to prepend `sudo` to docker commands.

Steps:

* `pull.sh` -- pull the appropriate MySQL Docker image.  Note that a pre-MySQL-8 version (5.7.22) is being used intentionally because MySQL 8 has some password issue.
* `run.sh` -- run a Docker container using the image, mapping port 3306 on localhost to the same inside the image.  But connecting directly to that port won't work before we set up a non-root user with appropriate privileges.
* `add_recount_user.sh` -- adds user `recount` with silly password to the MySQL server running in the container
* `add_recount_db.sh` -- adds database named `recount`
* `kill.sh` -- shut down the container

Utilities:

* `connect.sh` -- get a bash shell on the running container.
* `list_users.sh` -- list all the MySQL users on the MySQL server running in the container
