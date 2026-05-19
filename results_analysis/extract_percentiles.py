#!/usr/bin/env python3
"""
Extract parameter combinations for percentile values from results files
Usage: python extract_percentiles.py <input_file> [options]

Examples:
  # Get top 10% of regular responses - output parameter combinations
  python extract_percentiles.py results.txt --regular top --regular-pct 90
  
  # Get bottom 5% of adaptive responses
  python extract_percentiles.py results.txt --adaptive bottom --adaptive-pct 5
  
  # Get top 20% of regular AND bottom 15% of adaptive
  python extract_percentiles.py results.txt --regular top --regular-pct 80 --adaptive bottom --adaptive-pct 15
"""

import pandas as pd
import numpy as np
import argparse
import sys

def read_results_file(filepath):
    """Read results file and return dataframe with regular and adaptive columns"""
    
    # Find first non-comment line to determine column count
    with open(filepath, 'r') as f:
        for line in f:
            if not line.startswith('#'):
                first_data_line = line.strip()
                break
        n_cols = len(first_data_line.split())
    
    # Read data
    if n_cols == 7:
        df = pd.read_csv(filepath, comment='#', sep='\s+')
        df.columns = ['r', 'm', 'c', 'k', 'y', 'a', 'regular']
        df['adaptive'] = None
        has_adaptive = False
    elif n_cols == 8:
        df = pd.read_csv(filepath, comment='#', sep='\s+')
        df.columns = ['r', 'm', 'c', 'k', 'y', 'a', 'regular', 'adaptive']
        has_adaptive = True
    else:
        raise ValueError(f"Expected 7 or 8 columns, found {n_cols}")
    
    return df, has_adaptive

def format_k_value(k):
    """Format k value as integer with leading zeros (e.g., 0.050 -> 050, 0.5 -> 500)"""
    # Convert to integer after multiplying by 1000 to preserve 3 digits
    # Handle both decimal and integer representations
    if k >= 1:
        # If k is already an integer (e.g., 50), assume it's already multiplied by 1000?
        # Based on your sample: k=500 in file, k_actual=5.00? Let me check the pattern
        # Your sample shows: "1000 170 500 5 20000 1" - k=5 in file, but column says k=500?
        # Actually looking at your mse_results: k column has 500, but you want 050 (which is 0.50?)
        pass
    
    # Based on your example: you want "050" for k=500 in the file
    # That suggests k in file is already multiplied by 100? (500/100 = 5.00? No, 500/1000 = 0.5)
    # Let me assume: file k value needs to be divided by 1000 to get actual ratio
    # But you want 3 digits: 0.050 -> 050, 0.500 -> 500
    
    # Convert to actual ratio first (divide by 100 if k>1, else use as is)
    if k > 1:
        actual_k = k / 100.0  # Because your sample shows 500 -> 5.00
    else:
        actual_k = k
    
    # Now format as 3-digit integer (multiply by 100 to get 2 decimal places? No, you want 050 for 0.50)
    # For 0.050 -> 050 (that's 50 when interpreted as integer, but with leading zero)
    # For 5.00 -> 500 (that's 500 as integer)
    
    # Multiply by 100 to get 2 decimal places as integer
    k_int = int(round(actual_k * 100))
    return f"{k_int:03d}"

def extract_percentile_parameters(df, column_name, percentile, tail='top'):
    """
    Extract parameter combinations based on percentile and tail
    
    Parameters:
    -----------
    df : DataFrame
        The dataframe with parameter columns
    column_name : str
        Name of the response column ('regular' or 'adaptive')
    percentile : float
        Percentile threshold (0-100)
    tail : str
        'top' for values above the percentile
        'bottom' for values below the percentile
    
    Returns:
    --------
    list: List of formatted parameter strings
    """
    values = df[column_name].dropna().values
    
    if len(values) == 0:
        return []
    
    if tail.lower() == 'top':
        # Top N%: values above the (100-percentile)th percentile
        threshold = np.percentile(values, 100 - percentile)
        filtered_df = df[df[column_name] >= threshold]
    elif tail.lower() == 'bottom':
        # Bottom N%: values below the percentile-th percentile
        threshold = np.percentile(values, percentile)
        filtered_df = df[df[column_name] <= threshold]
    else:
        raise ValueError("tail must be 'top' or 'bottom'")
    
    # Extract parameter combinations
    param_lines = []
    for _, row in filtered_df.iterrows():
        # Format each parameter
        r = int(row['r'])
        m = int(row['m'])
        c = int(row['c'])
        k = format_k_value(row['k'])  # Format k with leading zeros
        y = int(row['y'])
        a = int(row['a']) if row['a'] == int(row['a']) else row['a']
        
        # For a, if it's integer, format as integer, otherwise keep as float
        if a == int(a):
            a = int(a)
        
        param_lines.append(f"{r} {m} {c} {k} {y} {a}")
    
    return param_lines

def main():
    parser = argparse.ArgumentParser(
        description='Extract parameter combinations for percentile values from results files',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument('input_file', help='Path to results .txt file')
    
    # Regular response options
    parser.add_argument('--regular', choices=['top', 'bottom'], 
                       help='Extract top or bottom percentiles from regular response')
    parser.add_argument('--regular-pct', type=float, 
                       help='Percentile for regular response (0-100, e.g., 90 for top 10%%)')
    
    # Adaptive response options
    parser.add_argument('--adaptive', choices=['top', 'bottom'],
                       help='Extract top or bottom percentiles from adaptive response')
    parser.add_argument('--adaptive-pct', type=float,
                       help='Percentile for adaptive response (0-100, e.g., 90 for top 10%%)')
    
    args = parser.parse_args()
    
    # Validate arguments
    if not args.regular and not args.adaptive:
        print("Error: Must specify at least one of --regular or --adaptive", file=sys.stderr)
        parser.print_help()
        sys.exit(1)
    
    if args.regular and args.regular_pct is None:
        print("Error: --regular-pct is required when using --regular", file=sys.stderr)
        sys.exit(1)
    
    if args.adaptive and args.adaptive_pct is None:
        print("Error: --adaptive-pct is required when using --adaptive", file=sys.stderr)
        sys.exit(1)
    
    if args.regular_pct and (args.regular_pct < 0 or args.regular_pct > 100):
        print("Error: --regular-pct must be between 0 and 100", file=sys.stderr)
        sys.exit(1)
    
    if args.adaptive_pct and (args.adaptive_pct < 0 or args.adaptive_pct > 100):
        print("Error: --adaptive-pct must be between 0 and 100", file=sys.stderr)
        sys.exit(1)
    
    # Read the file
    try:
        df, has_adaptive = read_results_file(args.input_file)
    except Exception as e:
        print(f"Error reading file: {e}", file=sys.stderr)
        sys.exit(1)
    
    all_parameters = []
    
    # Process regular response
    if args.regular:
        regular_params = extract_percentile_parameters(
            df, 'regular', args.regular_pct, args.regular
        )
        all_parameters.extend(regular_params)
        
        # Print info to stderr
        print(f"Regular: extracted {len(regular_params)} parameter sets ({args.regular} {args.regular_pct}%)", file=sys.stderr)
    
    # Process adaptive response
    if args.adaptive:
        if not has_adaptive:
            print("Error: File does not contain adaptive response column (need 8 columns)", file=sys.stderr)
            sys.exit(1)
        
        adaptive_params = extract_percentile_parameters(
            df, 'adaptive', args.adaptive_pct, args.adaptive
        )
        all_parameters.extend(adaptive_params)
        
        # Print info to stderr
        print(f"Adaptive: extracted {len(adaptive_params)} parameter sets ({args.adaptive} {args.adaptive_pct}%)", file=sys.stderr)
    
    # Output the parameter combinations (one per line)
    if all_parameters:
        for param_line in all_parameters:
            print(param_line)
    else:
        print("No parameters extracted", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
