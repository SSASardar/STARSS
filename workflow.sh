#!/bin/bash
set -e
rm "outputs/"*".txt"
echo "Running make test command centre."
echo 3 | make test

echo "Running make test evalu scans"
echo 4 | make test

echo "Running Python script..."

python visualisations/testB_nc.py
python visualisations/emp_vpr_animation.py
