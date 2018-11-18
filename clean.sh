#!/usr/bin/env bash

set -ex

find . -name __pycache__ | xargs rm -rf
find . -name '.pytest_cache' | xargs rm -rf
find . -name '*.pyc' | xargs rm -f
