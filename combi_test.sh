#!/bin/bash
set -e
rm "outputs/"*".txt"
echo "Running make test multi radar pcl."

START_TIME=$(date +%s)
echo 7 | make test
END_TIME=$(date +%s)

ELAPSED=$((END_TIME - START_TIME))
echo "Elapsed time: ${ELAPSED} seconds"
