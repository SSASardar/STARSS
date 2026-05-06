#!/bin/bash# Script to generate parameter combinations for batch testing
# Usage: ./generate_params.sh

CONFIG_FILE="config.txt"
PARAMS_FILE="params.txt"

# Initialize arrays for parameters
r_values=()
m_values=()
c_values=()
k_values=()
y_values=()
a_values=()

# Variables to store ranges
r_min=""; r_max=""; r_intervals=""
m_min=""; m_max=""; m_intervals=""
c_min=""; c_max=""; c_intervals=""
k_min=""; k_max=""; k_intervals=""
y_min=""; y_max=""; y_intervals=""
a_min=""; a_max=""; a_intervals=""

# Function to generate values from min, max, and intervals
generate_values() {
    local min=$1
    local max=$2
    local intervals=$3
    local -a result=()
    
    if [ $intervals -eq 0 ]; then
        # Only test at minimum value
        result+=($min)
    else
        # Calculate step size
        local step=$(echo "scale=10; ($max - $min) / $intervals" | bc)
        
        for i in $(seq 0 $intervals); do
            local value=$(echo "scale=2; $min + $i * $step" | bc)
            # Remove trailing .00 if present
            value=$(echo $value | sed 's/\.00$//' | sed 's/\.0$//')
            result+=($value)
        done
    fi
    
    # Return the array by printing values
    echo "${result[@]}"
}

# Function to ask for variable configuration
ask_variable() {
    local var_name=$1
    local var_display=$2
    local var_unit=$3
    local default_min=$4
    local default_max=$5
    local default_intervals=$6
    
    echo ""
    echo "========================================="
    echo "Configure $var_display ($var_name)"
    echo "========================================="
    
    # Ask if we should test this variable
    read -p "Test $var_display? (y/n) [y]: " test_var
    test_var=${test_var:-y}
    
    if [[ $test_var == "y" || $test_var == "Y" ]]; then
        read -p "  Minimum $var_display $var_unit [$default_min]: " min_val
        min_val=${min_val:-$default_min}
        
        read -p "  Maximum $var_display $var_unit [$default_max]: " max_val
        max_val=${max_val:-$default_max}
        
        read -p "  Number of intervals (0 = test only minimum) [$default_intervals]: " intervals
        intervals=${intervals:-$default_intervals}
        
        # Store the ranges
        eval "${var_name}_min=$min_val"
        eval "${var_name}_max=$max_val"
        eval "${var_name}_intervals=$intervals"
        
        # Generate values
        values=$(generate_values "$min_val" "$max_val" "$intervals")
        eval "${var_name}_values=($values)"
        
        local count=$(eval "echo \${#${var_name}_values[@]}")
        echo "  ✓ Will test $count values for $var_display"
        echo "  Values: $values"
        
        return 0
    else
        # Use default single value
        eval "${var_name}_min=$default_min"
        eval "${var_name}_max=$default_min"
        eval "${var_name}_intervals=0"
        
        values=$(generate_values "$default_min" "$default_min" "0")
        eval "${var_name}_values=($values)"
        
        echo "  → Using default value: $default_min"
        return 1
    fi
}

# Function to generate all combinations
generate_combinations() {
    local output_file=$1
    
    echo "Generating all combinations..."
    > $output_file
    
    # Get array sizes
    local r_count=${#r_values[@]}
    local m_count=${#m_values[@]}
    local c_count=${#c_values[@]}
    local k_count=${#k_values[@]}
    local y_count=${#y_values[@]}
    local a_count=${#a_values[@]}
    
    local total=$((r_count * m_count * c_count * k_count * y_count * a_count))
    
    echo "Total combinations to generate: $total"
    echo ""
    
    local count=0
    for r in "${r_values[@]}"; do
        for m in "${m_values[@]}"; do
            for c in "${c_values[@]}"; do
                for k in "${k_values[@]}"; do
                    for y in "${y_values[@]}"; do
                        for a in "${a_values[@]}"; do
                            echo "-r $r -m $m -c $c -k $k -y $y -a $a" >> $output_file
                            count=$((count + 1))
                            if [ $((count % 100)) -eq 0 ]; then
                                echo "  Generated $count combinations..."
                            fi
                        done
                    done
                done
            done
        done
    done
    
    echo ""
    echo "✅ Generated $count combinations"
    echo "✅ Saved to: $output_file"
}

# Function to save configuration
save_config() {
    local config_file=$1
    
    cat > $config_file << EOF
# Parameter configuration file
# Generated on: $(date)
# ==========================================

# Grid resolution (meters) - r
R_MIN=$r_min
R_MAX=$r_max
R_INTERVALS=$r_intervals
R_VALUES=${r_values[@]}

# Mature phase end time (minutes) - m
M_MIN=$m_min
M_MAX=$m_max
M_INTERVALS=$m_intervals
M_VALUES=${m_values[@]}

# Cloud base height (meters) - c
C_MIN=$c_min
C_MAX=$c_max
C_INTERVALS=$c_intervals
C_VALUES=${c_values[@]}

# Core circle ratio - k
K_MIN=$k_min
K_MAX=$k_max
K_INTERVALS=$k_intervals
K_VALUES=${k_values[@]}

# Raincell Y-distance (meters) - y
Y_MIN=$y_min
Y_MAX=$y_max
Y_INTERVALS=$y_intervals
Y_VALUES=${y_values[@]}

# Apparent motion - a
A_MIN=$a_min
A_MAX=$a_max
A_INTERVALS=$a_intervals
A_VALUES=${a_values[@]}

# Total combinations: $(( ${#r_values[@]} * ${#m_values[@]} * ${#c_values[@]} * ${#k_values[@]} * ${#y_values[@]} * ${#a_values[@]} ))
EOF

    echo "✅ Configuration saved to: $config_file"
}

# Main script
echo "========================================="
echo "  PARAMETER COMBINATION GENERATOR"
echo "========================================="
echo ""
echo "This script will help you generate parameter combinations"
echo "for batch testing your radar simulation."
echo ""

# Ask for each variable
ask_variable "r" "Grid resolution" "(meters)" "1000" "2000" "4"
ask_variable "m" "Mature phase end" "(minutes)" "170" "190" "3"
ask_variable "c" "Cloud base height" "(meters)" "500" "700" "3"
ask_variable "k" "Core circle ratio" "(0-1)" "0.5" "0.8" "3"
ask_variable "y" "Raincell Y-distance" "(meters)" "70000" "90000" "3"
ask_variable "a" "Apparent motion" "" "10" "15" "3"

# Show summary
echo ""
echo "========================================="
echo "  SUMMARY"
echo "========================================="
echo "Parameters to test:"
echo "  r (grid resolution):     ${#r_values[@]} values: ${r_values[@]}"
echo "  m (mature phase end):    ${#m_values[@]} values: ${m_values[@]}"
echo "  c (cloud base height):   ${#c_values[@]} values: ${c_values[@]}"
echo "  k (core ratio):          ${#k_values[@]} values: ${k_values[@]}"
echo "  y (Y-distance):          ${#y_values[@]} values: ${y_values[@]}"
echo "  a (apparent motion):     ${#a_values[@]} values: ${a_values[@]}"
echo ""

if [ ${#r_values[@]} -eq 0 ] || [ ${#m_values[@]} -eq 0 ] || [ ${#c_values[@]} -eq 0 ] || [ ${#k_values[@]} -eq 0 ] || [ ${#y_values[@]} -eq 0 ] || [ ${#a_values[@]} -eq 0 ]; then
    echo "❌ Error: All variables must have at least one value"
    echo "Please run the script again and ensure all variables are configured"
    exit 1
fi

total_combinations=$((${#r_values[@]} * ${#m_values[@]} * ${#c_values[@]} * ${#k_values[@]} * ${#y_values[@]} * ${#a_values[@]}))
echo "Total combinations: $total_combinations"
echo ""

# Confirm before generating
read -p "Generate parameter combinations? (y/n) [y]: " confirm
confirm=${confirm:-y}

if [[ $confirm == "y" || $confirm == "Y" ]]; then
    generate_combinations $PARAMS_FILE
    save_config $CONFIG_FILE
    
    echo ""
    echo "========================================="
    echo "  NEXT STEPS"
    echo "========================================="
    echo "1. Review the generated files:"
    echo "   - $CONFIG_FILE (your configuration)"
    echo "   - $PARAMS_FILE (parameter combinations)"
    echo ""
    echo "2. Run batch test with:"
    echo "   make batch-test TEST=test_cl PARAM_FILE=$PARAMS_FILE"
    echo ""
    echo "3. Or view first few combinations:"
    echo "   head -5 $PARAMS_FILE"
else
    echo "Cancelled."
    exit 0
fi
