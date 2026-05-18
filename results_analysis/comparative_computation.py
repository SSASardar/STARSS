#!/usr/bin/env python3
"""
Complete Analysis for 5-Factor Full Factorial Design
Reads from emd_results.txt, auto-detects levels, generates all plots
Now supports adaptive EMD column and range filtering
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from matplotlib import cm
import seaborn as sns
import statsmodels.api as sm
from statsmodels.formula.api import ols
import sys
import os
from datetime import datetime
from itertools import combinations
import argparse

# Redirect output to file
class Tee:
    def __init__(self, filename):
        self.terminal = sys.stdout
        self.log = open(filename, 'w', encoding='utf-8')
    
    def write(self, message):
        self.terminal.write(message)
        self.log.write(message)
        self.log.flush()
    
    def flush(self):
        self.terminal.flush()
        self.log.flush()

def read_emd_results(filepath, filter_params=None):
    """Read consolidated emd_results.txt with optional filtering"""
    # First read with flexible column handling
    with open(filepath, 'r') as f:
        first_line = f.readline().strip()
    
    # Determine number of columns
    if '#' in first_line:
        # Skip comment lines to find data line
        with open(filepath, 'r') as f:
            for line in f:
                if not line.startswith('#'):
                    first_data_line = line.strip()
                    break
        n_cols = len(first_data_line.split())
    else:
        n_cols = len(first_line.split())
    
    # Read CSV with appropriate column names
    if n_cols == 7:
        df = pd.read_csv(filepath, comment='#', sep='\s+')
        df.columns = ['r', 'm', 'c', 'k', 'y', 'a', 'emd']
        df['emd_adaptive'] = None  # No adaptive column
        print("Detected 7 columns: Regular EMD only")
    elif n_cols == 8:
        df = pd.read_csv(filepath, comment='#', sep='\s+')
        df.columns = ['r', 'm', 'c', 'k', 'y', 'a', 'emd', 'emd_adaptive']
        print("Detected 8 columns: Regular EMD and Adaptive EMD")
    else:
        raise ValueError(f"Expected 7 or 8 columns, found {n_cols}")
    
    # Convert k to actual value (divide by 100 if needed)
    if df['k'].max() > 1:
        df['k_actual'] = df['k'] / 100.0
    else:
        df['k_actual'] = df['k']
    
    # Apply range filtering if specified
    original_len = len(df)
    if filter_params:
        filter_mask = pd.Series([True] * len(df))
        
        if 'y_min' in filter_params and filter_params['y_min'] is not None:
            filter_mask &= df['y'] >= filter_params['y_min']
            print(f"Filtering: y >= {filter_params['y_min']}")
        
        if 'y_max' in filter_params and filter_params['y_max'] is not None:
            filter_mask &= df['y'] <= filter_params['y_max']
            print(f"Filtering: y <= {filter_params['y_max']}")
        
        if 'emd_min' in filter_params and filter_params['emd_min'] is not None:
            filter_mask &= df['emd'] >= filter_params['emd_min']
            print(f"Filtering: emd >= {filter_params['emd_min']}")
        
        if 'emd_max' in filter_params and filter_params['emd_max'] is not None:
            filter_mask &= df['emd'] <= filter_params['emd_max']
            print(f"Filtering: emd <= {filter_params['emd_max']}")
        
        df = df[filter_mask]
        print(f"Filter applied: {original_len} -> {len(df)} runs")
    
    return df

def auto_detect_levels(df, response_type='emd'):
    """Detect factor levels from data"""
    factors = {
        'r': 'Grid Resolution (m)',
        'm': 'Mature Phase End (min)',
        'c': 'Cloud Base Height (m)',
        'k_actual': 'Core Ratio',
        'y': 'Y-Distance (m)',
        'a': 'Apparent Motion'
    }
    
    levels = {}
    print("\n" + "="*80)
    print(f"DETECTED FACTOR LEVELS (for {response_type})")
    print("="*80)
    
    for factor, name in factors.items():
        if factor in df.columns:
            unique_vals = sorted(df[factor].unique())
            levels[factor] = unique_vals
            if factor == 'k_actual':
                print(f"{name:<25} {len(unique_vals):>3} levels: {[f'{x:.3f}' for x in unique_vals]}")
            elif factor in ['r', 'm', 'c', 'y', 'a']:
                if factor == 'a':
                    print(f"{name:<25} {len(unique_vals):>3} levels: {[f'{x:.1f}' for x in unique_vals]}")
                else:
                    print(f"{name:<25} {len(unique_vals):>3} levels: {[int(x) for x in unique_vals]}")
    
    return levels

def main_effects_plot(df, output_dir, response_type='emd', suffix=''):
    """Create main effects plots for all factors with consistent y-axis"""
    factors = ['r', 'm', 'c', 'k_actual', 'y', 'a']
    titles = ['Grid Resolution (m)', 'Mature Phase End (min)', 
              'Cloud Base Height (m)', 'Core Ratio (k)', 
              'Y-Distance (m)', 'Apparent Motion']
    
    # Calculate global EMD range for consistent y-axis
    global_emin = df[response_type].min()
    global_emax = df[response_type].max()
    y_margin = (global_emax - global_emin) * 0.1
    y_min = global_emin - y_margin
    y_max = global_emax + y_margin
    
    fig, axes = plt.subplots(2, 3, figsize=(18, 10))
    axes = axes.flatten()
    
    for idx, (factor, title) in enumerate(zip(factors, titles)):
        if factor in df.columns:
            means = df.groupby(factor)[response_type].mean()
            stds = df.groupby(factor)[response_type].std()
            
            ax = axes[idx]
            
            if factor == 'k_actual':
                x_labels = [f'{x:.3f}' for x in means.index]
                x_pos = range(len(means))
                ax.errorbar(x_pos, means.values, yerr=stds.values, 
                           fmt='o-', capsize=5, capthick=2, markersize=8, linewidth=2)
                ax.set_xticks(x_pos)
                ax.set_xticklabels(x_labels, rotation=45)
            else:
                ax.errorbar(means.index, means.values, yerr=stds.values, 
                           fmt='o-', capsize=5, capthick=2, markersize=8, linewidth=2)
            
            ax.set_xlabel(title)
            ax.set_ylabel(f'Mean {response_type.upper()}')
            ax.set_title(f'Main Effect: {factor}')
            ax.grid(True, alpha=0.3)
            ax.set_ylim(y_min, y_max)  # Consistent y-axis
            
            # Add value labels
            for i, (x, y) in enumerate(zip(means.index, means.values)):
                if factor == 'k_actual':
                    ax.annotate(f'{y:.5f}', (x_pos[i], y), xytext=(0, 10), 
                               textcoords='offset points', ha='center', fontsize=8)
                else:
                    ax.annotate(f'{y:.5f}', (x, y), xytext=(0, 10), 
                               textcoords='offset points', ha='center', fontsize=8)
    
    # Hide unused subplot if any
    if len(factors) < 6:
        axes[-1].set_visible(False)
    
    plt.tight_layout()
    output_file = os.path.join(output_dir, f'main_effects_plots{suffix}.png')
    plt.savefig(output_file, dpi=150)
    plt.close()
    print(f"✓ Main effects plots for {response_type} saved to: {output_file}")

def interaction_plots(df, output_dir, response_type='emd', suffix=''):
    """Create interaction plots for top factor pairs with consistent y-axis"""
    factors = ['c', 'k_actual', 'y', 'a', 'm']
    factor_names = {
        'c': 'Cloud Base (m)',
        'k_actual': 'Core Ratio',
        'y': 'Y-Distance (m)',
        'a': 'Motion',
        'm': 'Mature Phase (min)'
    }
    
    # Calculate all two-way interactions
    interactions = []
    for f1, f2 in combinations(factors, 2):
        if f1 in df.columns and f2 in df.columns:
            # Compute interaction strength
            df_temp = df.groupby([f1, f2])[response_type].mean().reset_index()
            f1_levels = len(df[f1].unique())
            f2_levels = len(df[f2].unique())
            
            # Estimate interaction magnitude
            pivot = df.pivot_table(values=response_type, index=f1, columns=f2, aggfunc='mean')
            if len(pivot) > 1 and len(pivot.columns) > 1:
                # Calculate interaction as variance of differences
                differences = pivot.diff(axis=1).diff(axis=0).fillna(0)
                strength = differences.abs().sum().sum()
                interactions.append((f1, f2, strength))
    
    # Sort by interaction strength and take top 8
    interactions.sort(key=lambda x: x[2], reverse=True)
    top_interactions = interactions[:8]
    
    print(f"\nTop 8 interactions by magnitude ({response_type}):")
    for f1, f2, strength in top_interactions:
        print(f"  {f1} × {f2}: {strength:.6f}")
    
    # Calculate global EMD range for consistent y-axis
    global_emin = df[response_type].min()
    global_emax = df[response_type].max()
    y_margin = (global_emax - global_emin) * 0.1
    y_min = global_emin - y_margin
    y_max = global_emax + y_margin
    
    # Create plots
    n_plots = len(top_interactions)
    n_cols = min(3, n_plots)
    n_rows = (n_plots + n_cols - 1) // n_cols
    
    fig, axes = plt.subplots(n_rows, n_cols, figsize=(6*n_cols, 5*n_rows))
    if n_plots == 1:
        axes = [axes]
    else:
        axes = axes.flatten()
    
    for idx, (f1, f2, strength) in enumerate(top_interactions):
        ax = axes[idx]
        
        # Pivot table for interaction
        pivot = df.pivot_table(values=response_type, index=f1, columns=f2, aggfunc='mean')
        
        # Plot each line
        for col in pivot.columns:
            if f2 == 'k_actual':
                label = f'{f2}={col:.3f}'
            elif f2 in ['m', 'c', 'y']:
                label = f'{f2}={col:.0f}'
            elif f2 == 'a':
                label = f'{f2}={col:.1f}'
            else:
                label = f'{f2}={col}'
            
            ax.plot(pivot.index, pivot[col], 'o-', linewidth=2, markersize=6, label=label)
        
        # Formatting
        if f1 == 'k_actual':
            ax.set_xticklabels([f'{x:.3f}' for x in pivot.index], rotation=45)
        
        ax.set_xlabel(factor_names.get(f1, f1))
        ax.set_ylabel(f'Mean {response_type.upper()}')
        ax.set_title(f'Interaction: {f1} × {f2}\n(strength={strength:.4f})')
        ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left', fontsize=8)
        ax.grid(True, alpha=0.3)
        ax.set_ylim(y_min, y_max)  # Consistent y-axis
    
    # Hide unused subplots
    for idx in range(len(top_interactions), len(axes)):
        axes[idx].set_visible(False)
    
    plt.tight_layout()
    output_file = os.path.join(output_dir, f'interaction_plots{suffix}.png')
    plt.savefig(output_file, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"✓ Interaction plots for {response_type} saved to: {output_file}")

def pareto_ranking(df, output_dir, response_type='emd', suffix=''):
    """Create Pareto chart of standardized effects with mean EMD reference line"""
    # Standardize all factors
    factors = ['c', 'k_actual', 'y', 'a', 'm']
    df_scaled = df.copy()
    
    for factor in factors:
        if factor in df.columns:
            mean = df[factor].mean()
            std = df[factor].std()
            if std > 0:
                df_scaled[f'{factor}_std'] = (df[factor] - mean) / std
    
    # Build linear model with standardized coefficients
    formula_terms = [f'{f}_std' for f in factors if f'{f}_std' in df_scaled.columns]
    
    # Add interactions (top 10 based on correlation)
    from itertools import combinations
    interactions = []
    for f1, f2 in combinations(factors, 2):
        if f'{f1}_std' in df_scaled.columns and f'{f2}_std' in df_scaled.columns:
            col1 = df_scaled[f'{f1}_std']
            col2 = df_scaled[f'{f2}_std']
            corr = np.corrcoef(col1, df_scaled[response_type])[0,1]
            corr2 = np.corrcoef(col2, df_scaled[response_type])[0,1]
            interactions.append((f1, f2, abs(corr) + abs(corr2)))
    
    interactions.sort(key=lambda x: x[2], reverse=True)
    top_interactions = interactions[:10]
    
    for f1, f2, _ in top_interactions:
        formula_terms.append(f'{f1}_std:{f2}_std')
    
    formula = f'{response_type} ~ ' + ' + '.join(formula_terms)
    
    model = ols(formula, data=df_scaled).fit()
    
    # Extract coefficients (excluding intercept)
    coefs = model.params[1:]
    names = model.params.index[1:]
    
    # Convert to numpy arrays for proper indexing
    coef_array = coefs.values
    name_array = names.values
    
    # Sort by absolute value
    sorted_idx = np.argsort(np.abs(coef_array))[::-1]
    sorted_names = name_array[sorted_idx]
    sorted_coefs = coef_array[sorted_idx]
    sorted_abs = np.abs(coef_array[sorted_idx])
    
    # Calculate percentage
    total_abs = np.sum(sorted_abs)
    percentages = (sorted_abs / total_abs) * 100
    
    # Calculate mean response
    mean_response = df[response_type].mean()
    
    # Create Pareto chart
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 8))
    
    # Bar chart
    colors = ['red' if x < 0 else 'green' for x in sorted_coefs]
    bars = ax1.bar(range(len(sorted_coefs)), sorted_coefs, color=colors, alpha=0.7)
    ax1.axhline(y=0, color='black', linestyle='-', linewidth=0.5)
    
    # Add mean response reference line
    ax1.text(0.02, 0.98, f'Mean {response_type.upper()} = {mean_response:.6f}', 
             transform=ax1.transAxes, fontsize=10, verticalalignment='top',
             bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
    
    ax1.set_xticks(range(len(sorted_names)))
    ax1.set_xticklabels(sorted_names, rotation=45, ha='right', fontsize=9)
    ax1.set_ylabel('Standardized Coefficient')
    ax1.set_title(f'Pareto Chart: Standardized Effects ({response_type.upper()})')
    ax1.grid(True, alpha=0.3, axis='y')
    
    # Add value labels
    for bar, val in zip(bars, sorted_coefs):
        height = bar.get_height()
        ax1.annotate(f'{val:.4f}', xy=(bar.get_x() + bar.get_width()/2, height),
                    xytext=(0, 3 if height > 0 else -15),
                    textcoords="offset points", ha='center', va='bottom', fontsize=8)
    
    # Cumulative percentage plot
    cumulative = np.cumsum(percentages)
    ax2.bar(range(len(percentages)), percentages, alpha=0.7, label='Individual')
    ax2.plot(range(len(percentages)), cumulative, 'ro-', linewidth=2, label='Cumulative')
    ax2.set_xticks(range(len(sorted_names)))
    ax2.set_xticklabels(sorted_names, rotation=45, ha='right', fontsize=9)
    ax2.set_ylabel('Percentage of Total Effect (%)')
    ax2.set_xlabel('Effects')
    ax2.set_title(f'Pareto: Cumulative Effect Contribution ({response_type.upper()})')
    ax2.legend()
    ax2.grid(True, alpha=0.3, axis='y')
    
    # Add cumulative labels
    for i, (pct, cum) in enumerate(zip(percentages[:10], cumulative[:10])):
        ax2.annotate(f'{cum:.1f}%', (i, cum), xytext=(0, 5),
                    textcoords="offset points", ha='center', fontsize=8)
    
    plt.tight_layout()
    output_file = os.path.join(output_dir, f'pareto_chart{suffix}.png')
    plt.savefig(output_file, dpi=150)
    plt.close()
    print(f"✓ Pareto chart for {response_type} saved to: {output_file}")
    
    # Print ranking
    print("\n" + "="*80)
    print(f"PARETO RANKING ({response_type.upper()}) - Standardized Coefficients")
    print("="*80)
    print(f"\n{'Rank':<6} {'Effect':<30} {'Coefficient':>12} {'|Coef|':>12} {'% of Total':>12}")
    print("-"*80)
    
    for i, (name, coef, pct) in enumerate(zip(sorted_names, sorted_coefs, percentages), 1):
        print(f"{i:<6} {name:<30} {coef:>12.6f} {abs(coef):>12.6f} {pct:>11.1f}%")
    
    return model, sorted_names, sorted_coefs, percentages

def response_surface_overview(df, output_dir, response_type='emd', suffix=''):
    """Create overview of all response surface pairs with consistent z-axis"""
    # Get all factors
    factors = ['c', 'k_actual', 'y', 'a', 'm']
    available = [f for f in factors if f in df.columns]
    
    if len(available) < 2:
        print("Not enough factors for 3D plots")
        return
    
    # Generate all combinations of factor pairs
    from itertools import combinations
    all_pairs = list(combinations(available, 2))
    
    print(f"\nGenerating overview of {len(all_pairs)} response surface pairs for {response_type}...")
    
    # Create centered data for prediction
    df_centered = df.copy()
    means = {}
    for factor in available:
        means[factor] = df[factor].mean()
        df_centered[f'{factor}_c'] = df[factor] - means[factor]
    
    # Build quadratic model for prediction
    formula_terms = []
    for factor in available:
        formula_terms.append(f'{factor}_c')
        formula_terms.append(f'I({factor}_c**2)')
    
    for f1, f2 in combinations(available, 2):
        formula_terms.append(f'{f1}_c:{f2}_c')
    
    formula = f'{response_type} ~ ' + ' + '.join(formula_terms)
    full_model = ols(formula, data=df_centered).fit()
    
    # Calculate global response range for consistent z-axis
    global_rmin = df[response_type].min()
    global_rmax = df[response_type].max()
    z_margin = (global_rmax - global_rmin) * 0.1
    z_min = global_rmin - z_margin
    z_max = global_rmax + z_margin
    
    # Calculate how many rows and columns for subplots
    n_plots = len(all_pairs)
    n_cols = min(3, n_plots)
    n_rows = (n_plots + n_cols - 1) // n_cols
    
    # Create figure with subplots for 3D surfaces
    fig = plt.figure(figsize=(6*n_cols, 5*n_rows))
    
    # Create a mapping for nicer labels
    factor_labels = {
        'c': 'Cloud Base Height (m)',
        'k_actual': 'Core Ratio (k)',
        'y': 'Y-Distance (m)',
        'a': 'Apparent Motion',
        'm': 'Mature Phase (min)'
    }
    
    for idx, (f1, f2) in enumerate(all_pairs):
        ax = fig.add_subplot(n_rows, n_cols, idx+1, projection='3d')
        
        # Create grid
        f1_vals = np.linspace(df[f1].min(), df[f1].max(), 30)
        f2_vals = np.linspace(df[f2].min(), df[f2].max(), 30)
        F1, F2 = np.meshgrid(f1_vals, f2_vals)
        Z = np.zeros_like(F1)
        
        # Fix other factors at mean
        for i in range(len(f1_vals)):
            for j in range(len(f2_vals)):
                pred_dict = {f'{f}_c': 0 for f in available}
                pred_dict[f'{f1}_c'] = f1_vals[i] - means[f1]
                pred_dict[f'{f2}_c'] = f2_vals[j] - means[f2]
                pred_df = pd.DataFrame([pred_dict])
                Z[j, i] = full_model.predict(pred_df)[0]
        
        # Plot surface with consistent z limits
        surf = ax.plot_surface(F1, F2, Z, cmap=cm.viridis, alpha=0.8, linewidth=0, antialiased=True)
        ax.set_zlim(z_min, z_max)  # Consistent z-axis
        
        # Labels with better formatting
        ax.set_xlabel(factor_labels.get(f1, f1), fontsize=9)
        ax.set_ylabel(factor_labels.get(f2, f2), fontsize=9)
        ax.set_zlabel(response_type.upper(), fontsize=9)
        
        # Calculate effect range for title
        effect_range = Z.max() - Z.min()
        ax.set_title(f'{f1} × {f2}\n(range: {effect_range:.5f})', fontsize=10)
        
        # Add colorbar
        fig.colorbar(surf, ax=ax, shrink=0.5, aspect=10)
    
    plt.tight_layout()
    output_file = os.path.join(output_dir, f'response_surfaces_overview{suffix}.png')
    plt.savefig(output_file, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"✓ Response surface overview for {response_type} saved to: {output_file}")
    
    # Create contour plot overview (2D)
    fig, axes = plt.subplots(n_rows, n_cols, figsize=(6*n_cols, 5*n_rows))
    if n_plots == 1:
        axes = [axes]
    else:
        axes = axes.flatten()
    
    for idx, (f1, f2) in enumerate(all_pairs):
        ax = axes[idx]
        
        # Create grid
        f1_vals = np.linspace(df[f1].min(), df[f1].max(), 50)
        f2_vals = np.linspace(df[f2].min(), df[f2].max(), 50)
        F1, F2 = np.meshgrid(f1_vals, f2_vals)
        Z = np.zeros_like(F1)
        
        # Fix other factors at mean
        for i in range(len(f1_vals)):
            for j in range(len(f2_vals)):
                pred_dict = {f'{f}_c': 0 for f in available}
                pred_dict[f'{f1}_c'] = f1_vals[i] - means[f1]
                pred_dict[f'{f2}_c'] = f2_vals[j] - means[f2]
                pred_df = pd.DataFrame([pred_dict])
                Z[j, i] = full_model.predict(pred_df)[0]
        
        # Contour plot with consistent levels
        levels = np.linspace(z_min, z_max, 20)
        contour = ax.contour(F1, F2, Z, levels=levels, cmap='viridis')
        ax.clabel(contour, inline=True, fontsize=8)
        ax.set_xlabel(factor_labels.get(f1, f1), fontsize=9)
        ax.set_ylabel(factor_labels.get(f2, f2), fontsize=9)
        
        # Mark minimum point
        min_idx = np.unravel_index(np.argmin(Z), Z.shape)
        ax.plot(f1_vals[min_idx[1]], f2_vals[min_idx[0]], 'r*', markersize=10, label='Minimum')
        
        effect_range = Z.max() - Z.min()
        ax.set_title(f'{f1} × {f2}\n(range: {effect_range:.5f})', fontsize=9)
        ax.legend(fontsize=8)
    
    # Hide unused subplots
    for idx in range(len(all_pairs), len(axes)):
        axes[idx].set_visible(False)
    
    plt.tight_layout()
    contour_file = os.path.join(output_dir, f'contour_plots_overview{suffix}.png')
    plt.savefig(contour_file, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"✓ Contour plot overview for {response_type} saved to: {contour_file}")

def correlation_matrix(df, output_dir, response_type='emd', suffix=''):
    """Create correlation matrix heatmap"""
    # Select only numeric columns
    numeric_cols = ['r', 'm', 'c', 'k_actual', 'y', 'a', response_type]
    available_cols = [col for col in numeric_cols if col in df.columns]
    
    corr_matrix = df[available_cols].corr()
    
    fig, ax = plt.subplots(figsize=(10, 8))
    sns.heatmap(corr_matrix, annot=True, cmap='coolwarm', center=0,
                square=True, linewidths=1, cbar_kws={"shrink": 0.8},
                fmt='.3f', ax=ax)
    ax.set_title(f'Correlation Matrix: Parameters vs {response_type.upper()}')
    
    plt.tight_layout()
    output_file = os.path.join(output_dir, f'correlation_matrix{suffix}.png')
    plt.savefig(output_file, dpi=150)
    plt.close()
    print(f"✓ Correlation matrix for {response_type} saved to: {output_file}")

def find_optimal_combination(df, output_dir, response_type='emd', suffix=''):
    """Find optimal parameter combination from data"""
    # Find best in data
    best_idx = df[response_type].idxmin()
    best = df.loc[best_idx]
    
    print("\n" + "="*80)
    print(f"OPTIMAL PARAMETER COMBINATION ({response_type.upper()} - Lowest Value)")
    print("="*80)
    print(f"\nGrid Resolution (r):     {best['r']:.0f}")
    print(f"Mature Phase End (m):     {best['m']:.0f} minutes")
    print(f"Cloud Base Height (c):    {best['c']:.0f} m")
    print(f"Core Ratio (k):           {best['k_actual']:.3f}")
    print(f"Y-Distance (y):           {best['y']:.0f} m")
    print(f"Apparent Motion (a):      {best['a']:.1f}")
    print(f"{response_type.upper()} Value:                {best[response_type]:.8f}")
    
    # Find worst in data
    worst_idx = df[response_type].idxmax()
    worst = df.loc[worst_idx]
    
    print("\n" + "="*80)
    print(f"WORST PARAMETER COMBINATION ({response_type.upper()} - Highest Value)")
    print("="*80)
    print(f"\nGrid Resolution (r):     {worst['r']:.0f}")
    print(f"Mature Phase End (m):     {worst['m']:.0f} minutes")
    print(f"Cloud Base Height (c):    {worst['c']:.0f} m")
    print(f"Core Ratio (k):           {worst['k_actual']:.3f}")
    print(f"Y-Distance (y):           {worst['y']:.0f} m")
    print(f"Apparent Motion (a):      {worst['a']:.1f}")
    print(f"{response_type.upper()} Value:                {worst[response_type]:.8f}")
    
    return best, worst

def save_summary(df, model, percentages, best, worst, output_dir, response_type='emd', suffix=''):
    """Save complete summary to text file"""
    summary_file = os.path.join(output_dir, f'analysis_summary_{response_type}{suffix}.txt')
    
    with open(summary_file, 'w') as f:
        f.write("="*80 + "\n")
        f.write(f"COMPLETE FACTORIAL ANALYSIS SUMMARY ({response_type.upper()})\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("="*80 + "\n\n")
        
        f.write(f"Total runs analyzed: {len(df)}\n")
        f.write(f"{response_type.upper()} range: {df[response_type].min():.8f} - {df[response_type].max():.8f}\n")
        f.write(f"{response_type.upper()} mean: {df[response_type].mean():.8f} ± {df[response_type].std():.8f}\n\n")
        
        f.write("="*80 + "\n")
        f.write(f"OPTIMAL COMBINATION (Lowest {response_type.upper()})\n")
        f.write("="*80 + "\n")
        f.write(f"r (Grid Resolution):     {best['r']:.0f}\n")
        f.write(f"m (Mature Phase End):    {best['m']:.0f} minutes\n")
        f.write(f"c (Cloud Base Height):   {best['c']:.0f} m\n")
        f.write(f"k (Core Ratio):          {best['k_actual']:.3f}\n")
        f.write(f"y (Y-Distance):          {best['y']:.0f} m\n")
        f.write(f"a (Apparent Motion):     {best['a']:.1f}\n")
        f.write(f"{response_type.upper()}:                     {best[response_type]:.8f}\n\n")
        
        f.write("="*80 + "\n")
        f.write(f"WORST COMBINATION (Highest {response_type.upper()})\n")
        f.write("="*80 + "\n")
        f.write(f"r (Grid Resolution):     {worst['r']:.0f}\n")
        f.write(f"m (Mature Phase End):    {worst['m']:.0f} minutes\n")
        f.write(f"c (Cloud Base Height):   {worst['c']:.0f} m\n")
        f.write(f"k (Core Ratio):          {worst['k_actual']:.3f}\n")
        f.write(f"y (Y-Distance):          {worst['y']:.0f} m\n")
        f.write(f"a (Apparent Motion):     {worst['a']:.1f}\n")
        f.write(f"{response_type.upper()}:                     {worst[response_type]:.8f}\n\n")
        
        f.write("="*80 + "\n")
        f.write("FACTOR LEVELS\n")
        f.write("="*80 + "\n")
        factors = ['r', 'm', 'c', 'k_actual', 'y', 'a']
        for factor in factors:
            if factor in df.columns:
                levels = sorted(df[factor].unique())
                if factor == 'k_actual':
                    f.write(f"{factor:<12}: {len(levels)} levels: {[f'{x:.3f}' for x in levels]}\n")
                elif factor == 'a':
                    f.write(f"{factor:<12}: {len(levels)} levels: {[f'{x:.1f}' for x in levels]}\n")
                else:
                    f.write(f"{factor:<12}: {len(levels)} levels: {[int(x) for x in levels]}\n")
        
        f.write("\n" + "="*80 + "\n")
        f.write("TOP 10 EFFECTS (Pareto Ranking)\n")
        f.write("="*80 + "\n\n")
        f.write("See pareto chart for complete ranking\n")
    
    print(f"✓ Complete summary for {response_type} saved to: {summary_file}")

def analyze_response(df, output_dir, response_type, suffix, filter_desc=""):
    """Run complete analysis for a given response type"""
    print("\n" + "="*80)
    print(f"ANALYZING {response_type.upper()}{filter_desc}")
    print("="*80)
    
    # Auto-detect levels
    levels = auto_detect_levels(df, response_type)
    
    # Generate all plots and analyses
    print("\n" + "="*80)
    print(f"GENERATING ANALYSES AND PLOTS FOR {response_type.upper()}")
    print("="*80)
    
    main_effects_plot(df, output_dir, response_type, suffix)
    interaction_plots(df, output_dir, response_type, suffix)
    correlation_matrix(df, output_dir, response_type, suffix)
    model, effect_names, effect_coefs, percentages = pareto_ranking(df, output_dir, response_type, suffix)
    response_surface_overview(df, output_dir, response_type, suffix)
    best, worst = find_optimal_combination(df, output_dir, response_type, suffix)
    save_summary(df, model, percentages, best, worst, output_dir, response_type, suffix)
    
    return best, worst

def main():
    parser = argparse.ArgumentParser(description='Analyze 5-factor factorial design results')
    parser.add_argument('input_file', help='Path to emd_results.txt file')
    parser.add_argument('--y-min', type=float, help='Minimum Y-distance filter')
    parser.add_argument('--y-max', type=float, help='Maximum Y-distance filter')
    parser.add_argument('--emd-min', type=float, help='Minimum EMD filter (for regular EMD)')
    parser.add_argument('--emd-max', type=float, help='Maximum EMD filter (for regular EMD)')
    parser.add_argument('--adaptive-only', action='store_true', help='Only analyze adaptive EMD column')
    parser.add_argument('--regular-only', action='store_true', help='Only analyze regular EMD column')
    
    args = parser.parse_args()
    
    filepath = args.input_file
    
    # Get batch folder
    batch_folder = os.path.dirname(filepath)
    if not batch_folder:
        batch_folder = os.getcwd()
    
    # Set up output redirection
    output_log = os.path.join(batch_folder, 'analysis_complete_output.txt')
    tee = Tee(output_log)
    sys.stdout = tee
    
    print("="*80)
    print("COMPLETE 5-FACTOR ANALYSIS WITH ADAPTIVE EMD SUPPORT")
    print("="*80)
    print(f"\nInput file: {filepath}")
    print(f"Output directory: {batch_folder}")
    
    # Build filter parameters
    filter_params = {}
    if args.y_min is not None:
        filter_params['y_min'] = args.y_min
    if args.y_max is not None:
        filter_params['y_max'] = args.y_max
    if args.emd_min is not None:
        filter_params['emd_min'] = args.emd_min
    if args.emd_max is not None:
        filter_params['emd_max'] = args.emd_max
    
    if filter_params:
        print("\n" + "="*80)
        print("FILTERS APPLIED")
        print("="*80)
        for key, value in filter_params.items():
            print(f"  {key}: {value}")
    
    # Read data with filtering
    df = read_emd_results(filepath, filter_params if filter_params else None)
    print(f"\nLoaded {len(df)} runs")
    
    # Determine which responses to analyze
    has_adaptive = 'emd_adaptive' in df.columns and df['emd_adaptive'].notna().any()
    
    analyze_regular = not args.adaptive_only
    analyze_adaptive = has_adaptive and not args.regular_only
    
    if not analyze_regular and not analyze_adaptive:
        print("Error: No analysis selected. Use --regular-only, --adaptive-only, or neither for both.")
        sys.exit(1)
    
    # Create filter description string for filenames
    filter_desc = ""
    if filter_params:
        filter_parts = []
        if 'y_min' in filter_params:
            filter_parts.append(f"y{filter_params['y_min']:.0f}")
        if 'y_max' in filter_params:
            filter_parts.append(f"y{filter_params['y_max']:.0f}")
        if 'emd_min' in filter_params:
            filter_parts.append(f"em{filter_params['emd_min']:.0f}")
        if 'emd_max' in filter_params:
            filter_parts.append(f"em{filter_params['emd_max']:.0f}")
        if filter_parts:
            filter_desc = "_" + "_".join(filter_parts)
    
    # Analyze regular EMD
    if analyze_regular:
        print("\n" + "="*80)
        print("ANALYZING REGULAR EMD")
        print("="*80)
        
        # Create a copy with only regular EMD data
        df_regular = df[df['emd'].notna()].copy()
        
        if len(df_regular) > 0:
            analyze_response(df_regular, batch_folder, 'emd', filter_desc, filter_desc)
        else:
            print("No valid regular EMD data found")
    
    # Analyze adaptive EMD
    if analyze_adaptive:
        print("\n" + "="*80)
        print("ANALYZING ADAPTIVE EMD")
        print("="*80)
        
        # Create a copy with only adaptive EMD data
        df_adaptive = df[df['emd_adaptive'].notna()].copy()
        
        if len(df_adaptive) > 0:
            analyze_response(df_adaptive, batch_folder, 'emd_adaptive', f"_adaptive{filter_desc}", f" (Adaptive){filter_desc}")
        else:
            print("No valid adaptive EMD data found")
    
    # Comparison summary if both are analyzed
    if analyze_regular and analyze_adaptive and len(df_regular) > 0 and len(df_adaptive) > 0:
        print("\n" + "="*80)
        print("REGULAR vs ADAPTIVE EMD COMPARISON")
        print("="*80)
        
        print(f"\nRegular EMD - Range: {df_regular['emd'].min():.8f} - {df_regular['emd'].max():.8f}")
        print(f"Regular EMD - Mean: {df_regular['emd'].mean():.8f} ± {df_regular['emd'].std():.8f}")
        print(f"\nAdaptive EMD - Range: {df_adaptive['emd_adaptive'].min():.8f} - {df_adaptive['emd_adaptive'].max():.8f}")
        print(f"Adaptive EMD - Mean: {df_adaptive['emd_adaptive'].mean():.8f} ± {df_adaptive['emd_adaptive'].std():.8f}")
        
        # Correlation between regular and adaptive
        if len(df_regular) == len(df_adaptive):
            correlation = np.corrcoef(df_regular['emd'], df_adaptive['emd_adaptive'])[0,1]
            print(f"\nCorrelation between Regular and Adaptive EMD: {correlation:.6f}")
        
        # Create comparison plot
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))
        
        # Scatter plot
        ax1.scatter(df_regular['emd'], df_adaptive['emd_adaptive'], alpha=0.5)
        ax1.plot([df_regular['emd'].min(), df_regular['emd'].max()], 
                [df_regular['emd'].min(), df_regular['emd'].max()], 
                'r--', label='Perfect correlation')
        ax1.set_xlabel('Regular EMD')
        ax1.set_ylabel('Adaptive EMD')
        ax1.set_title('Regular vs Adaptive EMD')
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        
        # Distribution comparison
        ax2.hist(df_regular['emd'], bins=30, alpha=0.5, label='Regular', density=True)
        ax2.hist(df_adaptive['emd_adaptive'], bins=30, alpha=0.5, label='Adaptive', density=True)
        ax2.set_xlabel('EMD Value')
        ax2.set_ylabel('Density')
        ax2.set_title('EMD Distribution Comparison')
        ax2.legend()
        ax2.grid(True, alpha=0.3)
        
        plt.tight_layout()
        comparison_file = os.path.join(batch_folder, f'regular_vs_adaptive_comparison{filter_desc}.png')
        plt.savefig(comparison_file, dpi=150)
        plt.close()
        print(f"\n✓ Regular vs Adaptive comparison plot saved to: {comparison_file}")
    
    # Final summary
    print("\n" + "="*80)
    print("ANALYSIS COMPLETE")
    print("="*80)
    print(f"\nAll outputs saved to: {batch_folder}")
    print("\nGenerated files:")
    
    if analyze_regular:
        print(f"\nRegular EMD analysis:")
        print(f"  - analysis_summary_emd{filter_desc}.txt")
        print(f"  - main_effects_plots{filter_desc}.png")
        print(f"  - interaction_plots{filter_desc}.png")
        print(f"  - correlation_matrix{filter_desc}.png")
        print(f"  - pareto_chart{filter_desc}.png")
        print(f"  - response_surfaces_overview{filter_desc}.png")
        print(f"  - contour_plots_overview{filter_desc}.png")
    
    if analyze_adaptive:
        print(f"\nAdaptive EMD analysis:")
        print(f"  - analysis_summary_emd_adaptive{filter_desc}.txt")
        print(f"  - main_effects_plots_adaptive{filter_desc}.png")
        print(f"  - interaction_plots_adaptive{filter_desc}.png")
        print(f"  - correlation_matrix_adaptive{filter_desc}.png")
        print(f"  - pareto_chart_adaptive{filter_desc}.png")
        print(f"  - response_surfaces_overview_adaptive{filter_desc}.png")
        print(f"  - contour_plots_overview_adaptive{filter_desc}.png")
    
    if analyze_regular and analyze_adaptive:
        print(f"\nComparison:")
        print(f"  - regular_vs_adaptive_comparison{filter_desc}.png")
    
    print("="*80)
    
    # Restore stdout
    sys.stdout = tee.terminal

if __name__ == "__main__":
    main()
