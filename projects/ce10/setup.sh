#!/usr/bin/env bash

d=$(dirname $0)

if [[ ! -d ${HOME}/.mc ]] ; then
    echo "Copying minio config to ~/.mc"
    cp -r ${d}/config/.mc $HOME/
else
    echo "minio config dir ~/.mc already exists; skipping..."
fi

[[ ! -d ${HOME}/.aws ]] && mkdir -p ${HOME}/.aws

if [[ -f ${HOME}/.aws/config ]] ; then
    if grep -q minio ${HOME}/.aws/config ; then
        echo "minio already in ~/.aws/config / ~/.aws/credentials; skipping..."
    else
        echo "Installing AWS config in existing ~/.aws/config and ~/.aws/credentials"
        cat ${d}/config/.aws/config >> ~/.aws/config
        cat ${d}/config/.aws/credentials >> ~/.aws/credentials
    fi
else
    echo "Installing AWS config in ~/.aws/config and ~/.aws/credentials"
    cp ${d}/config/.aws/config ~/.aws/
    cp ${d}/config/.aws/credentials ~/.aws/
fi
