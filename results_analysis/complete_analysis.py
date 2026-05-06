#!/usr/bin/env python3
"""
Complete Analysis for 5-Factor Full Factorial Design
Reads from emd_results.txt, auto-detects levels, generates all plots
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

def read_emd_results(filepath):
    """Read consolidated emd_results.txt"""
    df = pd.read_csv(filepath, comment='#', sep='\s+')
    
    # Handle different column formats
    if len(df.columns) == 7:
        df.columns = ['r', 'm', 'c', 'k', 'y', 'a', 'emd']
    elif len(df.columns) == 8:
        # Might have extra column
        df.columns = ['r', 'm', 'c', 'k', 'y', 'a', 'emd', 'extra']
        df = df.drop('extra', axis=1)
    
    # Convert k to actual value (divide by 100 if needed)
    if df['k'].max() > 1:
        df['k_actual'] = df['k'] / 100.0
    else:
        df['k_actual'] = df['k']
    
    return df

def auto_detect_levels(df):
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
    print("DETECTED FACTOR LEVELS")
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

def main_effects_plot(df, output_dir):
    """Create main effects plots for all factors"""
    factors = ['r', 'm', 'c', 'k_actual', 'y', 'a']
    titles = ['Grid Resolution (m)', 'Mature Phase End (min)', 
              'Cloud Base Height (m)', 'Core Ratio (k)', 
              'Y-Distance (m)', 'Apparent Motion']
    
    fig, axes = plt.subplots(2, 3, figsize=(18, 10))
    axes = axes.flatten()
    
    for idx, (factor, title) in enumerate(zip(factors, titles)):
        if factor in df.columns:
            means = df.groupby(factor)['emd'].mean()
            stds = df.groupby(factor)['emd'].std()
            
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
            ax.set_ylabel('Mean EMD')
            ax.set_title(f'Main Effect: {factor}')
            ax.grid(True, alpha=0.3)
            
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
    output_file = os.path.join(output_dir, 'main_effects_plots.png')
    plt.savefig(output_file, dpi=150)
    plt.close()
    print(f"✓ Main effects plots saved to: {output_file}")

def interaction_plots(df, output_dir):
    """Create interaction plots for top factor pairs"""
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
            df_temp = df.groupby([f1, f2])['emd'].mean().reset_index()
            f1_levels = len(df[f1].unique())
            f2_levels = len(df[f2].unique())
            
            # Estimate interaction magnitude
            pivot = df.pivot_table(values='emd', index=f1, columns=f2, aggfunc='mean')
            if len(pivot) > 1 and len(pivot.columns) > 1:
                # Calculate interaction as variance of differences
                differences = pivot.diff(axis=1).diff(axis=0).fillna(0)
                strength = differences.abs().sum().sum()
                interactions.append((f1, f2, strength))
    
    # Sort by interaction strength and take top 8
    interactions.sort(key=lambda x: x[2], reverse=True)
    top_interactions = interactions[:8]
    
    print(f"\nTop 8 interactions by magnitude:")
    for f1, f2, strength in top_interactions:
        print(f"  {f1} × {f2}: {strength:.6f}")
    
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
        pivot = df.pivot_table(values='emd', index=f1, columns=f2, aggfunc='mean')
        
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
        ax.set_ylabel('Mean EMD')
        ax.set_title(f'Interaction: {f1} × {f2}\n(strength={strength:.4f})')
        ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left', fontsize=8)
        ax.grid(True, alpha=0.3)
    
    # Hide unused subplots
    for idx in range(len(top_interactions), len(axes)):
        axes[idx].set_visible(False)
    
    plt.tight_layout()
    output_file = os.path.join(output_dir, 'interaction_plots.png')
    plt.savefig(output_file, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"✓ Interaction plots saved to: {output_file}")

def pareto_ranking(df, output_dir):
    """Create Pareto chart of standardized effects"""
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
            corr = np.corrcoef(col1, df_scaled['emd'])[0,1]
            corr2 = np.corrcoef(col2, df_scaled['emd'])[0,1]
            interactions.append((f1, f2, abs(corr) + abs(corr2)))
    
    interactions.sort(key=lambda x: x[2], reverse=True)
    top_interactions = interactions[:10]
    
    for f1, f2, _ in top_interactions:
        formula_terms.append(f'{f1}_std:{f2}_std')
    
    formula = 'emd ~ ' + ' + '.join(formula_terms)
    
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
    
    # Create Pareto chart
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 8))
    
    # Bar chart
    colors = ['red' if x < 0 else 'green' for x in sorted_coefs]
    bars = ax1.bar(range(len(sorted_coefs)), sorted_coefs, color=colors, alpha=0.7)
    ax1.axhline(y=0, color='black', linestyle='-', linewidth=0.5)
    ax1.set_xticks(range(len(sorted_names)))
    ax1.set_xticklabels(sorted_names, rotation=45, ha='right', fontsize=9)
    ax1.set_ylabel('Standardized Coefficient')
    ax1.set_title('Pareto Chart: Standardized Effects')
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
    ax2.set_title('Pareto: Cumulative Effect Contribution')
    ax2.legend()
    ax2.grid(True, alpha=0.3, axis='y')
    
    # Add cumulative labels
    for i, (pct, cum) in enumerate(zip(percentages[:10], cumulative[:10])):
        ax2.annotate(f'{cum:.1f}%', (i, cum), xytext=(0, 5),
                    textcoords="offset points", ha='center', fontsize=8)
    
    plt.tight_layout()
    output_file = os.path.join(output_dir, 'pareto_chart.png')
    plt.savefig(output_file, dpi=150)
    plt.close()
    print(f"✓ Pareto chart saved to: {output_file}")
    
    # Print ranking
    print("\n" + "="*80)
    print("PARETO RANKING (Standardized Coefficients)")
    print("="*80)
    print(f"\n{'Rank':<6} {'Effect':<30} {'Coefficient':>12} {'|Coef|':>12} {'% of Total':>12}")
    print("-"*80)
    
    for i, (name, coef, pct) in enumerate(zip(sorted_names, sorted_coefs, percentages), 1):
        print(f"{i:<6} {name:<30} {coef:>12.6f} {abs(coef):>12.6f} {pct:>11.1f}%")
    
    return model, sorted_names, sorted_coefs, percentages

def response_surface_3d(model, df, output_dir):
    """Create 3D response surface plots for ALL factor pairs"""
    # Get all factors
    factors = ['c', 'k_actual', 'y', 'a', 'm']
    available = [f for f in factors if f in df.columns]
    
    if len(available) < 2:
        print("Not enough factors for 3D plots")
        return
    
    # Generate all combinations of factor pairs
    from itertools import combinations
    all_pairs = list(combinations(available, 2))
    
    print(f"\nGenerating 3D surfaces for {len(all_pairs)} factor pairs...")
    
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
    
    formula = 'emd ~ ' + ' + '.join(formula_terms)
    full_model = ols(formula, data=df_centered).fit()
    
    # Calculate how many rows and columns for subplots
    n_plots = len(all_pairs)
    n_cols = min(3, n_plots)
    n_rows = (n_plots + n_cols - 1) // n_cols
    
    # Create figure with subplots
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
        
        # Plot surface
        surf = ax.plot_surface(F1, F2, Z, cmap=cm.viridis, alpha=0.8, linewidth=0, antialiased=True)
        
        # Labels with better formatting
        ax.set_xlabel(factor_labels.get(f1, f1), fontsize=9)
        ax.set_ylabel(factor_labels.get(f2, f2), fontsize=9)
        ax.set_zlabel('EMD', fontsize=9)
        
        # Calculate effect range for title
        effect_range = Z.max() - Z.min()
        ax.set_title(f'{f1} × {f2}\n(range: {effect_range:.5f})', fontsize=10)
        
        # Add colorbar
        fig.colorbar(surf, ax=ax, shrink=0.5, aspect=10)
    
    plt.tight_layout()
    output_file = os.path.join(output_dir, 'response_surfaces_3d_all_pairs.png')
    plt.savefig(output_file, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"✓ All {n_plots} 3D response surfaces saved to: {output_file}")
    
    # Also create a separate figure for each interaction (optional, for better detail)
    print("\nCreating detailed individual plots...")
    for idx, (f1, f2) in enumerate(all_pairs):
        fig = plt.figure(figsize=(10, 8))
        ax = fig.add_subplot(111, projection='3d')
        
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
        
        # Plot surface
        surf = ax.plot_surface(F1, F2, Z, cmap=cm.viridis, alpha=0.9, linewidth=0, antialiased=True)
        
        # Add contour projection on the bottom
        ax.contour(F1, F2, Z, zdir='z', offset=Z.min(), cmap=cm.viridis, alpha=0.5)
        
        ax.set_xlabel(factor_labels.get(f1, f1), fontsize=11)
        ax.set_ylabel(factor_labels.get(f2, f2), fontsize=11)
        ax.set_zlabel('EMD', fontsize=11)
        
        effect_range = Z.max() - Z.min()
        ax.set_title(f'Response Surface: {f1} × {f2}\n(EMD range: {effect_range:.6f})', fontsize=12)
        
        fig.colorbar(surf, ax=ax, shrink=0.6, aspect=15)
        
        # Save individual plot
        individual_file = os.path.join(output_dir, f'response_surface_{f1}_vs_{f2}.png')
        plt.savefig(individual_file, dpi=150, bbox_inches='tight')
        plt.close()
        
        if (idx + 1) % 5 == 0:
            print(f"  Generated {idx+1}/{len(all_pairs)} plots...")
    
    print(f"✓ Individual plots saved to: {output_dir}/response_surface_*_vs_*.png")
    
    # Also create a 2D contour plot summary
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
        
        # Contour plot
        contour = ax.contour(F1, F2, Z, levels=20, cmap='viridis')
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
    contour_file = os.path.join(output_dir, 'response_surfaces_contours_all_pairs.png')
    plt.savefig(contour_file, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"✓ Contour plots saved to: {contour_file}")

def find_optimal_combination(df, output_dir):
    """Find optimal parameter combination from data"""
    # Find best in data
    best_idx = df['emd'].idxmin()
    best = df.loc[best_idx]
    
    print("\n" + "="*80)
    print("OPTIMAL PARAMETER COMBINATION (From Data)")
    print("="*80)
    print(f"\nGrid Resolution (r):     {best['r']:.0f}")
    print(f"Mature Phase End (m):     {best['m']:.0f} minutes")
    print(f"Cloud Base Height (c):    {best['c']:.0f} m")
    print(f"Core Ratio (k):           {best['k_actual']:.3f}")
    print(f"Y-Distance (y):           {best['y']:.0f} m")
    print(f"Apparent Motion (a):      {best['a']:.1f}")
    print(f"EMD Value:                {best['emd']:.8f}")
    
    # Find worst in data
    worst_idx = df['emd'].idxmax()
    worst = df.loc[worst_idx]
    
    print("\n" + "="*80)
    print("WORST PARAMETER COMBINATION (From Data)")
    print("="*80)
    print(f"\nGrid Resolution (r):     {worst['r']:.0f}")
    print(f"Mature Phase End (m):     {worst['m']:.0f} minutes")
    print(f"Cloud Base Height (c):    {worst['c']:.0f} m")
    print(f"Core Ratio (k):           {worst['k_actual']:.3f}")
    print(f"Y-Distance (y):           {worst['y']:.0f} m")
    print(f"Apparent Motion (a):      {worst['a']:.1f}")
    print(f"EMD Value:                {worst['emd']:.8f}")
    
    return best, worst

def correlation_matrix(df, output_dir):
    """Create correlation matrix heatmap"""
    # Select only numeric columns
    numeric_cols = ['r', 'm', 'c', 'k_actual', 'y', 'a', 'emd']
    available_cols = [col for col in numeric_cols if col in df.columns]
    
    corr_matrix = df[available_cols].corr()
    
    fig, ax = plt.subplots(figsize=(10, 8))
    sns.heatmap(corr_matrix, annot=True, cmap='coolwarm', center=0,
                square=True, linewidths=1, cbar_kws={"shrink": 0.8},
                fmt='.3f', ax=ax)
    ax.set_title('Correlation Matrix: Parameters vs EMD')
    
    plt.tight_layout()
    output_file = os.path.join(output_dir, 'correlation_matrix.png')
    plt.savefig(output_file, dpi=150)
    plt.close()
    print(f"✓ Correlation matrix saved to: {output_file}")

def save_summary(df, model, percentages, best, worst, output_dir):
    """Save complete summary to text file"""
    summary_file = os.path.join(output_dir, 'analysis_complete_summary.txt')
    
    with open(summary_file, 'w') as f:
        f.write("="*80 + "\n")
        f.write("COMPLETE FACTORIAL ANALYSIS SUMMARY\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("="*80 + "\n\n")
        
        f.write(f"Total runs analyzed: {len(df)}\n")
        f.write(f"EMD range: {df['emd'].min():.8f} - {df['emd'].max():.8f}\n")
        f.write(f"EMD mean: {df['emd'].mean():.8f} ± {df['emd'].std():.8f}\n\n")
        
        f.write("="*80 + "\n")
        f.write("OPTIMAL COMBINATION (Lowest EMD)\n")
        f.write("="*80 + "\n")
        f.write(f"r (Grid Resolution):     {best['r']:.0f}\n")
        f.write(f"m (Mature Phase End):    {best['m']:.0f} minutes\n")
        f.write(f"c (Cloud Base Height):   {best['c']:.0f} m\n")
        f.write(f"k (Core Ratio):          {best['k_actual']:.3f}\n")
        f.write(f"y (Y-Distance):          {best['y']:.0f} m\n")
        f.write(f"a (Apparent Motion):     {best['a']:.1f}\n")
        f.write(f"EMD:                     {best['emd']:.8f}\n\n")
        
        f.write("="*80 + "\n")
        f.write("WORST COMBINATION (Highest EMD)\n")
        f.write("="*80 + "\n")
        f.write(f"r (Grid Resolution):     {worst['r']:.0f}\n")
        f.write(f"m (Mature Phase End):    {worst['m']:.0f} minutes\n")
        f.write(f"c (Cloud Base Height):   {worst['c']:.0f} m\n")
        f.write(f"k (Core Ratio):          {worst['k_actual']:.3f}\n")
        f.write(f"y (Y-Distance):          {worst['y']:.0f} m\n")
        f.write(f"a (Apparent Motion):     {worst['a']:.1f}\n")
        f.write(f"EMD:                     {worst['emd']:.8f}\n\n")
        
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
        
        # We need to recreate the ranking here
        # For now, placeholder
        f.write("See pareto_chart.png for complete ranking\n")
    
    print(f"✓ Complete summary saved to: {summary_file}")

def main():
    if len(sys.argv) != 2:
        print("Usage: python3 complete_analysis.py <emd_results_file>")
        print("Example: python3 complete_analysis.py batch_test_20260506_163028/emd_results.txt")
        sys.exit(1)
    
    filepath = sys.argv[1]
    
    # Get batch folder
    batch_folder = os.path.dirname(filepath)
    if not batch_folder:
        batch_folder = os.getcwd()
    
    # Set up output redirection
    output_log = os.path.join(batch_folder, 'analysis_complete_output.txt')
    tee = Tee(output_log)
    sys.stdout = tee
    
    print("="*80)
    print("COMPLETE 5-FACTOR ANALYSIS")
    print("="*80)
    print(f"\nInput file: {filepath}")
    print(f"Output directory: {batch_folder}")
    
    # Read data
    df = read_emd_results(filepath)
    print(f"\nLoaded {len(df)} runs")
    
    # Auto-detect levels
    levels = auto_detect_levels(df)
    
    # Generate all plots and analyses
    print("\n" + "="*80)
    print("GENERATING ANALYSES AND PLOTS")
    print("="*80)
    
    main_effects_plot(df, batch_folder)
    interaction_plots(df, batch_folder)
    correlation_matrix(df, batch_folder)
    model, effect_names, effect_coefs, percentages = pareto_ranking(df, batch_folder)
    response_surface_3d(model, df, batch_folder)
    best, worst = find_optimal_combination(df, batch_folder)
    save_summary(df, model, percentages, best, worst, batch_folder)
    
    # Final summary
    print("\n" + "="*80)
    print("ANALYSIS COMPLETE")
    print("="*80)
    print(f"\nAll outputs saved to: {batch_folder}")
    print("\nGenerated files:")
    print("  - analysis_complete_output.txt (console output)")
    print("  - analysis_complete_summary.txt (summary statistics)")
    print("  - main_effects_plots.png")
    print("  - interaction_plots.png")
    print("  - correlation_matrix.png")
    print("  - pareto_chart.png")
    print("  - response_surfaces_3d.png")
    print("="*80)
    
    # Restore stdout
    sys.stdout = tee.terminal

if __name__ == "__main__":
    main()
