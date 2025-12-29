#!/bin/bash
set -e
rm "outputs/"*".txt"
echo "Running make test with input 2..."
echo 3 | make test

echo "Running make test with input 3..."
echo 4 | make test

echo "Running Python script..."
python visualisations/testB.py
