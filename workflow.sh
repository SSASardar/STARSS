#!/bin/bash
set -e
rm "outputs/"*".txt"
echo "Running make test command centre."
echo 5 | make test

echo "Running make test evalu scans"
echo 6 | make test

echo "Running Python script..."

python visualisations/testB_nc.py
python visualisations/emp_vpr_animation.py

#echo "Running make test RHI_evaluation"
#echo 1 | make test

#python visualisations/RHI_Cartesian_animate.py
