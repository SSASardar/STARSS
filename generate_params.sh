#!/bin/bash
# Script to generate parameter combinations for batch testing
# Usage: ./generate_params.sh

CONFIG_FILE="config.txt"
PARAMS_FILE="params.txt"

# Initialize arrays for parameters
x1_values=()  # radius of raincell (km)
x2_values=()  # core ratio (0-1)
x3_values=()  # rain intensity (mm/hr)
x4_values=()  # apparent motion (m/s)
x5_values=()  # cloud base height (km)
x6_values=()  # distance to C-band radar (km)
x7_values=()  # storm duration (minutes)

# Variables to store ranges
x1_min=""; x1_max=""; x1_intervals=""
x2_min=""; x2_max=""; x2_intervals=""
x3_min=""; x3_max=""; x3_intervals=""
x4_min=""; x4_max=""; x4_intervals=""
x5_min=""; x5_max=""; x5_intervals=""
x6_min=""; x6_max=""; x6_intervals=""
x7_min=""; x7_max=""; x7_intervals=""

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
           #value=$(echo $value | sed 's/\.00$//' | sed 's/\.0$//')
	   value=$(printf "%.10g" $value)
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
    local c_default=$7  # Default value from C program if user skips testing
    
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
        # Use default value from C program
        eval "${var_name}_min=$c_default"
        eval "${var_name}_max=$c_default"
        eval "${var_name}_intervals=0"
        
        values=$(generate_values "$c_default" "$c_default" "0")
        eval "${var_name}_values=($values)"
        
        echo "  → Using default value: $c_default"
        return 1
    fi
}

# Function to edit a specific parameter
edit_parameter() {
    local var_name=$1
    local var_display=$2
    local var_unit=$3
    
    echo ""
    echo "========================================="
    echo "Edit $var_display ($var_name)"
    echo "========================================="
    echo "Current values: $(eval echo \${${var_name}_values[@]})"
    echo "Current min: $(eval echo \$${var_name}_min)"
    echo "Current max: $(eval echo \$${var_name}_max)"
    echo "Current intervals: $(eval echo \$${var_name}_intervals)"
    echo ""
    
    read -p "  New minimum $var_display $var_unit [$(eval echo \$${var_name}_min)]: " min_val
    min_val=${min_val:-$(eval echo \$${var_name}_min)}
    
    read -p "  New maximum $var_display $var_unit [$(eval echo \$${var_name}_max)]: " max_val
    max_val=${max_val:-$(eval echo \$${var_name}_max)}
    
    read -p "  New number of intervals [$(eval echo \$${var_name}_intervals)]: " intervals
    intervals=${intervals:-$(eval echo \$${var_name}_intervals)}
    
    # Update the ranges
    eval "${var_name}_min=$min_val"
    eval "${var_name}_max=$max_val"
    eval "${var_name}_intervals=$intervals"
    
    # Generate new values
    values=$(generate_values "$min_val" "$max_val" "$intervals")
    eval "${var_name}_values=($values)"
    
    local count=$(eval "echo \${#${var_name}_values[@]}")
    echo "  ✓ Updated: $count values for $var_display"
    echo "  New values: $values"
}

# Function to generate all combinations
generate_combinations() {
    local output_file=$1
    
    echo "Generating all combinations..."
    > $output_file
    
    # Get array sizes
    local x1_count=${#x1_values[@]}
    local x2_count=${#x2_values[@]}
    local x3_count=${#x3_values[@]}
    local x4_count=${#x4_values[@]}
    local x5_count=${#x5_values[@]}
    local x6_count=${#x6_values[@]}
    local x7_count=${#x7_values[@]}
    
    local total=$((x1_count * x2_count * x3_count * x4_count * x5_count * x6_count * x7_count))
    
    echo "Total combinations to generate: $total"
    echo ""
    
    local count=0
    for x1 in "${x1_values[@]}"; do
        for x2 in "${x2_values[@]}"; do
            for x3 in "${x3_values[@]}"; do
                for x4 in "${x4_values[@]}"; do
                    for x5 in "${x5_values[@]}"; do
                        for x6 in "${x6_values[@]}"; do
                            for x7 in "${x7_values[@]}"; do
                                echo "-a $x1 -b $x2 -c $x3 -d $x4 -e $x5 -f $x6 -g $x7" >> $output_file
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

# Radius of raincell (kilometers) - x1
X1_MIN=$x1_min
X1_MAX=$x1_max
X1_INTERVALS=$x1_intervals
X1_VALUES=${x1_values[@]}

# Core ratio (0-1) - x2
X2_MIN=$x2_min
X2_MAX=$x2_max
X2_INTERVALS=$x2_intervals
X2_VALUES=${x2_values[@]}

# Rain intensity (mm/hr) - x3
X3_MIN=$x3_min
X3_MAX=$x3_max
X3_INTERVALS=$x3_intervals
X3_VALUES=${x3_values[@]}

# Apparent motion (m/s) - x4
X4_MIN=$x4_min
X4_MAX=$x4_max
X4_INTERVALS=$x4_intervals
X4_VALUES=${x4_values[@]}

# Cloud base height (kilometers) - x5
X5_MIN=$x5_min
X5_MAX=$x5_max
X5_INTERVALS=$x5_intervals
X5_VALUES=${x5_values[@]}

# Distance to C-band radar (kilometers) - x6
X6_MIN=$x6_min
X6_MAX=$x6_max
X6_INTERVALS=$x6_intervals
X6_VALUES=${x6_values[@]}

# Storm duration (minutes) - x7
X7_MIN=$x7_min
X7_MAX=$x7_max
X7_INTERVALS=$x7_intervals
X7_VALUES=${x7_values[@]}

# Total combinations: $(( ${#x1_values[@]} * ${#x2_values[@]} * ${#x3_values[@]} * ${#x4_values[@]} * ${#x5_values[@]} * ${#x6_values[@]} * ${#x7_values[@]} ))
EOF

    echo "✅ Configuration saved to: $config_file"
}

# Function to show current parameter summary
show_parameter_summary() {
    echo ""
    echo "========================================="
    echo "  CURRENT PARAMETER SUMMARY"
    echo "========================================="
    echo "  x1 (raincell radius):     ${#x1_values[@]} values: ${x1_values[@]}"
    echo "  x2 (core ratio):          ${#x2_values[@]} values: ${x2_values[@]}"
    echo "  x3 (rain intensity):      ${#x3_values[@]} values: ${x3_values[@]}"
    echo "  x4 (apparent motion):     ${#x4_values[@]} values: ${x4_values[@]}"
    echo "  x5 (cloud base height):   ${#x5_values[@]} values: ${x5_values[@]}"
    echo "  x6 (distance to radar):   ${#x6_values[@]} values: ${x6_values[@]}"
    echo "  x7 (storm duration):      ${#x7_values[@]} values: ${x7_values[@]}"
    echo ""
    
    total_combinations=$((${#x1_values[@]} * ${#x2_values[@]} * ${#x3_values[@]} * ${#x4_values[@]} * ${#x5_values[@]} * ${#x6_values[@]} * ${#x7_values[@]}))
    echo "Total combinations: $total_combinations"
    echo "========================================="
}

# Function for post-configuration editing
post_config_editing() {
    local edit_another="y"
    
    while [[ $edit_another == "y" || $edit_another == "Y" ]]; do
        echo ""
        echo "========================================="
        echo "  POST-CONFIGURATION EDITING"
        echo "========================================="
        show_parameter_summary
        echo ""
        
        read -p "Do you want to edit a parameter? (y/n) [n]: " edit_param
        edit_param=${edit_param:-n}
        
        if [[ $edit_param != "y" && $edit_param != "Y" ]]; then
            break
        fi
        
        echo ""
        echo "Available parameters to edit:"
        echo "  1) Radius of raincell (x1)"
        echo "  2) Core ratio (x2)"
        echo "  3) Rain intensity (x3)"
        echo "  4) Apparent motion (x4)"
        echo "  5) Cloud base height (x5)"
        echo "  6) Distance to C-band radar (x6)"
        echo "  7) Storm duration (x7)"
        echo "  0) Cancel and generate"
        echo ""
        
        read -p "Select parameter (0-7): " param_choice
        
        case $param_choice in
            1)
                edit_parameter "x1" "Radius of raincell" "(km)"
                ;;
            2)
                edit_parameter "x2" "Core ratio" "(0-1)"
                ;;
            3)
                edit_parameter "x3" "Rain intensity" "(mm/hr)"
                ;;
            4)
                edit_parameter "x4" "Apparent motion" "(m/s)"
                ;;
            5)
                edit_parameter "x5" "Cloud base height" "(km)"
                ;;
            6)
                edit_parameter "x6" "Distance to C-band radar" "(km)"
                ;;
            7)
                edit_parameter "x7" "Storm duration" "(minutes)"
                ;;
            0)
                break
                ;;
            *)
                echo "Invalid choice. Please try again."
                continue
                ;;
        esac
        
        echo ""
        read -p "Edit another parameter? (y/n) [n]: " edit_another
        edit_another=${edit_another:-n}
    done
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
# Format: ask_variable "var_name" "Display name" "unit" "default_min" "default_max" "default_intervals" "C_program_default"
ask_variable "x1" "Radius of raincell" "(km)" "5" "15" "2" "10"
ask_variable "x2" "Core ratio" "(0-1)" "0.1" "0.5" "2" "0.3"
ask_variable "x3" "Rain intensity" "(mm/hr)" "20" "45" "2" "35"
ask_variable "x4" "Apparent motion" "(m/s)" "3" "15" "2" "9"
ask_variable "x5" "Cloud base height" "(km)" "2" "4" "2" "2"
ask_variable "x6" "Distance to C-band radar" "(km)" "15" "75" "2" "30"
ask_variable "x7" "Storm duration" "(minutes)" "20" "40" "2" "30"

# Show initial summary
echo ""
echo "========================================="
echo "  INITIAL CONFIGURATION COMPLETE"
echo "========================================="
show_parameter_summary

# Post-configuration editing
post_config_editing

# Final summary before generation
echo ""
echo "========================================="
echo "  FINAL CONFIGURATION"
echo "========================================="
show_parameter_summary

# Verify all variables have values
if [ ${#x1_values[@]} -eq 0 ] || [ ${#x2_values[@]} -eq 0 ] || [ ${#x3_values[@]} -eq 0 ] || [ ${#x4_values[@]} -eq 0 ] || [ ${#x5_values[@]} -eq 0 ] || [ ${#x6_values[@]} -eq 0 ] || [ ${#x7_values[@]} -eq 0 ]; then
    echo "❌ Error: All variables must have at least one value"
    echo "Please run the script again and ensure all variables are configured"
    exit 1
fi

total_combinations=$((${#x1_values[@]} * ${#x2_values[@]} * ${#x3_values[@]} * ${#x4_values[@]} * ${#x5_values[@]} * ${#x6_values[@]} * ${#x7_values[@]}))
echo ""
echo "Total combinations to generate: $total_combinations"
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
