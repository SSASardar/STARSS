#!/usr/bin/env python3
"""
Plot comparison between ad_stats_*.txt and stats_*.txt files for a given parameter combination.
Usage: python plot_stats_comparison.py <batch_directory>
"""

import os
import sys
import glob
import re
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

def extract_params_from_filename(filename):
    """Extract parameters from filename - handles leading zeros correctly"""
    basename = os.path.basename(filename)
    pattern = r'.*_r_(\d+)_m_(\d+)_c_(\d+)_k_(\d+)_y_(\d+)_a_(\d+)\.txt'
    match = re.search(pattern, basename)
    if match:
        return {
            'r': int(match.group(1)),
            'm': int(match.group(2)),
            'c': int(match.group(3)),
            'k': int(match.group(4)),
            'y': int(match.group(5)),
            'a': int(match.group(6))
        }
    return None

def format_params(params):
    """Format parameters for display"""
    return f"r={params['r']}, m={params['m']}, c={params['c']}, k={params['k']}, y={params['y']}, a={params['a']}"

def get_available_options(ad_files):
    """Extract all available values for each parameter from the filenames"""
    options = {
        'r': set(),
        'm': set(),
        'c': set(),
        'k': set(),
        'y': set(),
        'a': set()
    }
    
    param_list = []
    for f in ad_files:
        params = extract_params_from_filename(f)
        if params:
            param_list.append(params)
            for key in options:
                options[key].add(params[key])
    
    # Sort each set
    for key in options:
        options[key] = sorted(list(options[key]))
    
    return options, param_list

def select_parameter_interactive(options, param_list):
    """Interactive selection: choose values for each parameter one by one"""
    print("\n" + "="*70)
    print("📋 Available parameter values:")
    print("="*70)
    for param in ['r', 'm', 'c', 'k', 'y', 'a']:
        if len(options[param]) > 20:
            print(f"  {param}: {options[param][:10]}... (total {len(options[param])} values)")
        else:
            print(f"  {param}: {options[param]}")
    
    print("\n" + "="*70)
    print("🔍 Now select your parameter combination:")
    print("="*70)
    
    selected = {}
    for param in ['r', 'm', 'c', 'k', 'y', 'a']:
        while True:
            try:
                print(f"\n{param} options: {options[param]}")
                choice = input(f"Choose {param} (enter value): ").strip()
                
                val = int(choice)
                if val in options[param]:
                    selected[param] = val
                    break
                else:
                    print(f"❌ {val} not available. Choose from: {options[param]}")
            except ValueError:
                print(f"❌ Please enter a valid integer")
    
    print("\n" + "="*70)
    print(f"✅ Selected: {format_params(selected)}")
    print("="*70)
    
    return selected

def parse_direct_input(input_str):
    """Parse 6 space-separated values from direct input"""
    parts = input_str.strip().split()
    if len(parts) != 6:
        return None
    
    try:
        params = {
            'r': int(parts[0]),
            'm': int(parts[1]),
            'c': int(parts[2]),
            'k': int(parts[3]),
            'y': int(parts[4]),
            'a': int(parts[5])
        }
        return params
    except ValueError:
        return None

def select_parameters(options, param_list):
    """Main selection function - offers both interactive and direct input"""
    print("\n" + "="*70)
    print("🔍 Parameter Selection")
    print("="*70)
    print("\nHow would you like to select parameters?")
    print("  1) Interactive selection (choose each parameter one by one)")
    print("  2) Direct input (enter 6 space-separated values)")
    print("  3) Show all available combinations")
    
    while True:
        choice = input("\nYour choice (1/2/3): ").strip()
        
        if choice == '1':
            return select_parameter_interactive(options, param_list)
        
        elif choice == '2':
            print("\nEnter 6 space-separated values in order: r m c k y a")
            print(f"Example: {options['r'][0]} {options['m'][0]} {options['c'][0]} {options['k'][0]} {options['y'][0]} {options['a'][0]}")
            
            while True:
                direct_input = input("\nEnter values: ").strip()
                params = parse_direct_input(direct_input)
                
                if params is None:
                    print("❌ Invalid input. Please enter exactly 6 integers separated by spaces.")
                    continue
                
                # Validate that this combination exists
                if params in param_list:
                    print(f"\n✅ Selected: {format_params(params)}")
                    return params
                else:
                    print(f"❌ Combination {format_params(params)} not found!")
                    print("   Available combinations:")
                    for i, p in enumerate(param_list[:5]):
                        print(f"     {i+1}. {format_params(p)}")
                    if len(param_list) > 5:
                        print(f"     ... and {len(param_list)-5} more")
                    
                    retry = input("\nTry again? (y/n): ").strip().lower()
                    if retry != 'y':
                        break
        
        elif choice == '3':
            print("\n📋 All available parameter combinations:")
            print("-"*70)
            for i, params in enumerate(param_list):
                print(f"{i+1:4d}. {format_params(params)}")
                if i >= 49:  # Show first 50
                    print(f"     ... and {len(param_list)-50} more combinations")
                    break
            
            input("\nPress Enter to continue...")
            # Loop back to menu
        
        else:
            print("❌ Invalid choice. Please enter 1, 2, or 3.")

def find_matching_files(batch_dir, selected_params):
    """Find ad_stats and stats files matching the selected parameters"""
    all_ad_files = glob.glob(os.path.join(batch_dir, "ad_stats_*.txt"))
    all_stats_files = glob.glob(os.path.join(batch_dir, "stats_*.txt"))
    
    ad_file = None
    stats_file = None
    
    for f in all_ad_files:
        params = extract_params_from_filename(f)
        if params and params == selected_params:
            ad_file = f
            break
    
    for f in all_stats_files:
        params = extract_params_from_filename(f)
        if params and params == selected_params:
            stats_file = f
            break
    
    return ad_file, stats_file

def load_and_validate_data(ad_file, stats_file):
    """Load both files and validate columns"""
    df_ad = pd.read_csv(ad_file, sep=r'\s+', skiprows=1, 
                        names=['Scan', 'MSE', 'MAE', 'Bias', 'Total_meas', 
                               'Total_true_unmasked', 'Total_meas_mm2', 'Total_true_mm2_unmasked'])
    df_stats = pd.read_csv(stats_file, sep=r'\s+', skiprows=1,
                           names=['Scan', 'MSE', 'MAE', 'Bias', 'Total_meas',
                                  'Total_true_unmasked', 'Total_meas_mm2', 'Total_true_mm2_unmasked'])
    
    # Check last columns match
    if not np.allclose(df_ad['Total_true_mm2_unmasked'], df_stats['Total_true_mm2_unmasked']):
        print("⚠️ Warning: Last columns ('Total_true_mm2_unmasked') do not match between files!")
    
    return df_ad, df_stats

def create_comparison_figure(df_ad, df_stats, params):
    """Create the 3-panel comparison figure"""
    fig, axes = plt.subplots(3, 1, figsize=(14, 8), sharex=True)
    
    x = df_ad['Scan']
    
    # Plot 1: Total rainfall accumulation (mm² per unit area)
    axes[0].plot(x, df_ad['Total_meas_mm2'], 'b-o', label='ad_stats: Measured accumulation', markersize=3, linewidth=1)
    axes[0].plot(x, df_stats['Total_meas_mm2'], 'r-s', label='stats: Measured accumulation', markersize=3, linewidth=1)
    axes[0].plot(x, df_ad['Total_true_mm2_unmasked'], 'k--', label='Ground truth accumulation', linewidth=2, alpha=0.7)
    axes[0].set_ylabel('Accumulation (mm² per unit area)')
    axes[0].legend(loc='best', fontsize=9)
    axes[0].grid(True, alpha=0.3)
    axes[0].set_title(f'Total Rainfall Accumulation - {format_params(params)}', fontsize=10)
    
    # Plot 2: MSE (column 1)
    axes[1].plot(x, df_ad['MSE'], 'b-o', label='ad_stats MSE', markersize=3, linewidth=1)
    axes[1].plot(x, df_stats['MSE'], 'r-s', label='stats MSE', markersize=3, linewidth=1)
    axes[1].set_ylabel('MSE')
    axes[1].legend(loc='best', fontsize=9)
    axes[1].grid(True, alpha=0.3)
    axes[1].set_title('Mean Squared Error Comparison', fontsize=10)
    
    # Plot 3: Bias (column 3)
    axes[2].plot(x, df_ad['Bias'], 'b-o', label='ad_stats Bias', markersize=3, linewidth=1)
    axes[2].plot(x, df_stats['Bias'], 'r-s', label='stats Bias', markersize=3, linewidth=1)
    axes[2].set_xlabel('Scan / Timestep')
    axes[2].set_ylabel('Bias')
    axes[2].legend(loc='best', fontsize=9)
    axes[2].grid(True, alpha=0.3)
    axes[2].set_title('Bias Comparison', fontsize=10)
    
    plt.tight_layout()
    return fig

def main():
    if len(sys.argv) != 2:
        print("❌ Error: Please provide the batch directory as a command-line argument")
        print(f"Usage: {sys.argv[0]} <batch_directory>")
        print(f"Example: {sys.argv[0]} ./batch_results/")
        sys.exit(1)
    
    batch_dir = sys.argv[1]
    
    if not os.path.isdir(batch_dir):
        print(f"❌ Directory '{batch_dir}' not found!")
        sys.exit(1)
    
    print(f"📁 Searching for files in: {batch_dir}")
    
    # Find all ad_stats files
    ad_files = glob.glob(os.path.join(batch_dir, "ad_stats_*.txt"))
    if not ad_files:
        print(f"❌ No ad_stats_*.txt files found in '{batch_dir}'")
        sys.exit(1)
    
    print(f"✅ Found {len(ad_files)} ad_stats files")
    print(f"✅ Found {len(glob.glob(os.path.join(batch_dir, 'stats_*.txt')))} stats files")
    
    # Show a sample filename to verify pattern matching
    if ad_files:
        print(f"\n📄 Sample filename: {os.path.basename(ad_files[0])}")
        sample_params = extract_params_from_filename(ad_files[0])
        if sample_params:
            print(f"   Extracted: {format_params(sample_params)}")
        else:
            print(f"   ⚠️ Warning: Could not extract parameters from sample!")
    
    # Extract available combinations
    options, param_list = get_available_options(ad_files)
    
    if not param_list:
        print("❌ No valid parameter combinations found! Check filename format.")
        sys.exit(1)
    
    # Select parameters (interactive or direct)
    selected_params = select_parameters(options, param_list)
    
    if selected_params is None:
        print("\n❌ No parameter combination selected. Exiting.")
        sys.exit(1)
    
    # Find matching files
    ad_file, stats_file = find_matching_files(batch_dir, selected_params)
    
    if not ad_file:
        print(f"\n❌ No ad_stats file found for {format_params(selected_params)}")
        sys.exit(1)
    
    if not stats_file:
        print(f"\n❌ No stats file found for {format_params(selected_params)}")
        sys.exit(1)
    
    print(f"\n✅ Found files:")
    print(f"   ad_stats:  {os.path.basename(ad_file)}")
    print(f"   stats:     {os.path.basename(stats_file)}")
    
    # Load data
    df_ad, df_stats = load_and_validate_data(ad_file, stats_file)
    print(f"📊 Loaded {len(df_ad)} timesteps from each file")
    
    # Create plot
    fig = create_comparison_figure(df_ad, df_stats, selected_params)
    
    # Save or show
    save = input("\n💾 Save figure? (y/n): ").strip().lower()
    if save == 'y':
        safe_name = f"comparison_r{selected_params['r']}_m{selected_params['m']}_c{selected_params['c']}_k{selected_params['k']}_y{selected_params['y']}_a{selected_params['a']}.png"
        output_path = os.path.join(batch_dir, safe_name)
        plt.savefig(output_path, dpi=150, bbox_inches='tight')
        print(f"✅ Saved to {output_path}")
    
    plt.show()

if __name__ == "__main__":
    main()
