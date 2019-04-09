#!/bin/bash

for i in $(grep '^http.*zip$' README.md) ; do
    wget ${i}
    bi=$(basename ${i})
    unzip ${bi}
done
