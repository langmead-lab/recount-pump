#!/bin/bash

set -e

echo -n "HISAT2 check..."
hisat2 --version > hisat2.version
if grep -q '2.1.0$' hisat2.version ; then echo "PASSED" ; else echo "FAILED" ; fi

echo -n "MultiQC check..."
multiqc --version > multiqc.version 
if grep -q '1.3$' multiqc.version ; then echo "PASSED" ; else echo "FAILED" ; fi

echo -n "STAR check..."
STAR --version > star.version
if grep -q '2.5.3a' star.version ; then echo "PASSED" ; else echo "FAILED" ; fi

echo -n "bedgraphtobigwig check..."
(bedgraphtobigwig 2> bedgraphtobigwig.version) || true
if grep -q 'bedGraphToBigWig v 4' bedgraphtobigwig.version ; then echo "PASSED" ; else echo "FAILED" ; fi

echo -n "prefetch check..."
prefetch --version > prefetch.version
if grep -q '2.8.2$' prefetch.version ; then echo "PASSED" ; else echo "FAILED" ; fi
