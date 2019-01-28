#!/bin/sh

# Run this from a specific project directory while analysis jobs are underway.
# It parses the slurm*.out files for strings that typically indicate errors,
# and tallies the types of errors.

echo "=============="
echo "Rule-based"
echo "=============="
grep 'Error in rule' *.out | awk '{h[$NF] += 1} END {for(d in h) {print d,h[d]}}' | sort -n -k2,2
echo

echo "=============="
echo "Segfault-based"
echo "=============="
grep 'Segmentation fault' *.out | awk '{h[$14,$15] += 1} END {for(d in h) {print d,h[d]}}' | sort -n -k2,2
echo

echo "=============="
echo "Mem alloc message"
echo "=============="
cat *.out | grep -c 'Memory allocation failed'
echo

echo "=============="
echo "Alignment message"
echo "=============="
cat *.out | grep -c 'FATAL ERROR in reads input'
echo

echo "=============="
echo "Task failure based"
echo "=============="
grep -c 'INSERT INTO task_failure' *.out
