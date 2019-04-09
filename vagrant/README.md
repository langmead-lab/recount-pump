Two of the subdirectories (`build_integration` and `build_workflow`) contain `Vagrantfile`s for AWS-based activities.  The third (`recount-dev`) contains a `Vagrantfile` for setting up a Debian-based development environment in which it's easy to run `recount-pump` and its tests.

The AWS-based `Vagrantfile`s require some one-time setup.  Also, they should be invoked using the `vagrant_run.py` wrapper script.  That script helps by first setting certain AWS config-related environment variables, and by sending a Slack notification with a summary of how to run went. 

The `aws.json` file contains relevant AWS settings and IDs that are then used in the `Vagrantfile`s.  The contents checked in to the repo are specific to the Langmead Lab AWS setup, so you will need to modify if you do not have access to our account.  (None of what's in that file is secret.)

### AWS setup

For EC2-based Vagrant setups (`build_integration` and `build_workflow`), some preparation is needed:

* Create a VPC
    * I've used the block 172.31.0.0/16
    * Edit network ACL
* Create an internet gateway
    * Attach it to the VPC
* Create subnets within the VPC 
    * I've used /20 blocks like 172.31.0.0/20, 172.31.32.0/20, 172.31.64.0/20, ...
    * For each: Actions -> Modify auto-assign IP
        * Check box
* Associate a security group
* Add the internet gateway to the route table for the VPC
    * It has to already be "associated with the VPC"
    * Actions -> Edit Routes...

To run either `build_integration` or `build_workflow`, change to the subdirectory and run `../vagrant_run.py`.  See documentation for `../vagrant_run.py` for how to (a) suppress the Slack message, (b) switch AWS profiles, etc. 

### Set up `vagrant` for AWS

Special `vagrant` plugins are needed for AWS support and for EC2 spot support in particular.

```
vagrant plugin install vagrant-aws-mkubenka --plugin-version "0.7.2.pre.22"
vagrant box add dummy https://github.com/mitchellh/vagrant-aws/raw/master/dummy.box
```

### Set up Slack

By default, the `run_vagrant.py` script will publish status messages to our `recount-pump` Slack group.  The `vagrant_run.py` script expects a file called `~/.recount/slack.ini` to exist.  The file has this format:

```
[slack]
tstring=?????????
bstring=?????????
secret=????????????????????????
```

If you need a copy, ask other teammates for it.

### AWS troubleshooting

* Vagrant hangs on `Waiting for SSH to become available...`
    * Log into console and find record for EC2 instance
        * Are public DNS and public IP blank?
        * If so, double check that the subnets have "auto-assign public IP" box checked under Actions -> Modify auto-assign IP

