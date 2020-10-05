#!/bin/bash
set -x
cat current.droppedout | perl -ne 'chomp; $f=$_; `pushd $f ; ../vd ; ../restart.sh $f ; popd`;'
