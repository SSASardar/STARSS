#!/bin/bash
set -e
rm "outputs/"*".txt"
echo "Running make test multi_radar_ processing plc"
echo 7 | make test

echo "Running Python scripts..."

python visualisations/testB_nc.py
python visualisations/Aradar_comparison.py
python visualisations/emp_vpr_adaptive_animation.py

