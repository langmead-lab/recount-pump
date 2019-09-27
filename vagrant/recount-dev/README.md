A Debian Stretch Linux environment that makes it easier to develop for `recount-pump`, especially if you are working from a Mac where `singularity` doesn't work and where `docker` is limited in some key ways.

The VM has `docker` and `singularity` pre-installed.

To get the latest version of the monorail pipeline from quay.io:

`docker pull quay.io/benlangmead/recount-rs5`

It uses Vagrant's `config.vm.synced_folder` facility to share folders like this:

* `~/git/recount-pump` on host becomes `/home/vagrant/git/recount-pump` in VM
* `~/git/recount-unify` on host becomes `/home/vagrant/git/recount-unify` in VM

You may need to edit the host paths.

TODO:

* Allow `vagrant` user to use Docker
