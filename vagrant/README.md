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
