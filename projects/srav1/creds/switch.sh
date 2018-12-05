#!/bin/bash

for i in *.override ; do
    ibase=$(echo $i | sed 's/\.override$//')
    cp $ibase $ibase.bak
    cp $i $ibase
done
