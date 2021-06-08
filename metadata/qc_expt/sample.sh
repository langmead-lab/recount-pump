#!/usr/bin/env bash

awk 'BEGIN {srand()} !/^rail_id/ { if (rand() <= .05) print $0} /^rail_id/ {print}' samples.tsv > samples_sm.tsv
