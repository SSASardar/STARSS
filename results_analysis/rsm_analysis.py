#!/usr/bin/env python3
"""
Response Surface Methodology (RSM) & Effects Analysis for Deterministic Computer Experiments
No replicates needed - uses regression and effect estimation
All outputs saved to batch folder
"""

import pandas as pd
import numpy as np
from scipy import stats
import statsmodels.api as sm
from statsmodels.formula.api import ols
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from matplotlib import cm
import sys
import os
from datetime import datetime

# Redirect print output to both console and file
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
    """Read emd_results.txt and parse parameters"""
    try:
        df = pd.read_csv(filepath, comment='#', sep='\s+',
                         names=['r', 'm', 'c', 'k', 'y', 'a', 'emd'])
    except:
        df = pd.read_csv(filepath, comment='#', sep=None, engine='python')
        df.columns = ['r', 'm', 'c', 'k', 'y', 'a', 'emd']
    
    # Convert k to actual value (divide by 100)
    df['k_actual'] = df['k'] / 100.0
    
    return df

def effects_analysis(df):
    """Calculate main effects and two-way interactions without ANOVA"""
    print("\n" + "="*80)
    print("EFFECTS ANALYSIS (No Replicates)")
    print("="*80)
    
    factors = {
        'c': 'Cloud Base Height',
        'k_actual': 'Core Ratio',
        'y': 'Y-Distance'
    }
    
    results = []
    
    # Calculate main effects
    print("\nMAIN EFFECTS:")
    print("-"*60)
    print(f"{'Factor':<20} {'Low Level':>12} {'High Level':>12} {'Effect':>12} {'% of Total':>12}")
    print("-"*60)
    
    total_effect_magnitude = 0
    
    for factor, name in factors.items():
        levels = sorted(df[factor].unique())
        low_val = levels[0]
        high_val = levels[-1]
        
        low_mean = df[df[factor] == low_val]['emd'].mean()
        high_mean = df[df[factor] == high_val]['emd'].mean()
        
        effect = high_mean - low_mean
        effect_magnitude = abs(effect)
        total_effect_magnitude += effect_magnitude
        
        results.append({
            'type': 'Main',
            'factor': name,
            'effect': effect,
            'magnitude': effect_magnitude,
            'direction': 'positive' if effect > 0 else 'negative'
        })
        
        print(f"{name:<20} {low_val:>12.0f} {high_val:>12.0f} {effect:>12.6f} ")
    
    # Calculate interaction effects
    print("\n\nTWO-WAY INTERACTIONS:")
    print("-"*80)
    print(f"{'Interaction':<30} {'Low-Low':>15} {'High-High':>15} {'Effect':>12}")
    print("-"*80)
    
    # c × k interaction
    c_levels = sorted(df['c'].unique())
    k_levels = sorted(df['k_actual'].unique())
    
    c_low, c_high = c_levels[0], c_levels[-1]
    k_low, k_high = k_levels[0], k_levels[-1]
    
    # Effect of c at low k
    c_effect_low_k = (df[(df['c'] == c_high) & (df['k_actual'] == k_low)]['emd'].mean() - 
                      df[(df['c'] == c_low) & (df['k_actual'] == k_low)]['emd'].mean())
    
    # Effect of c at high k
    c_effect_high_k = (df[(df['c'] == c_high) & (df['k_actual'] == k_high)]['emd'].mean() - 
                       df[(df['c'] == c_low) & (df['k_actual'] == k_high)]['emd'].mean())
    
    interaction_ck = (c_effect_high_k - c_effect_low_k) / 2
    
    # c × y interaction
    y_levels = sorted(df['y'].unique())
    y_low, y_high = y_levels[0], y_levels[-1]
    
    c_effect_low_y = (df[(df['c'] == c_high) & (df['y'] == y_low)]['emd'].mean() - 
                      df[(df['c'] == c_low) & (df['y'] == y_low)]['emd'].mean())
    
    c_effect_high_y = (df[(df['c'] == c_high) & (df['y'] == y_high)]['emd'].mean() - 
                       df[(df['c'] == c_low) & (df['y'] == y_high)]['emd'].mean())
    
    interaction_cy = (c_effect_high_y - c_effect_low_y) / 2
    
    # k × y interaction
    k_effect_low_y = (df[(df['k_actual'] == k_high) & (df['y'] == y_low)]['emd'].mean() - 
                      df[(df['k_actual'] == k_low) & (df['y'] == y_low)]['emd'].mean())
    
    k_effect_high_y = (df[(df['k_actual'] == k_high) & (df['y'] == y_high)]['emd'].mean() - 
                       df[(df['k_actual'] == k_low) & (df['y'] == y_high)]['emd'].mean())
    
    interaction_ky = (k_effect_high_y - k_effect_low_y) / 2
    
    print(f"{'c × k':<30} {f'c={c_low:.0f},k={k_low:.3f}':>15} {f'c={c_high:.0f},k={k_high:.3f}':>15} {interaction_ck:>12.6f}")
    print(f"{'c × y':<30} {f'c={c_low:.0f},y={y_low:.0f}':>15} {f'c={c_high:.0f},y={y_high:.0f}':>15} {interaction_cy:>12.6f}")
    print(f"{'k × y':<30} {f'k={k_low:.3f},y={y_low:.0f}':>15} {f'k={k_high:.3f},y={y_high:.0f}':>15} {interaction_ky:>12.6f}")
    
    # Update magnitude totals
    for effect, mag in [('c×k', abs(interaction_ck)), ('c×y', abs(interaction_cy)), ('k×y', abs(interaction_ky))]:
        total_effect_magnitude += mag
        results.append({
            'type': 'Interaction',
            'factor': effect,
            'effect': effect,
            'magnitude': mag
        })
    
    # Calculate percentage contribution
    print("\n" + "="*80)
    print("RELATIVE IMPORTANCE (Percentage of Total Effect Magnitude)")
    print("="*80)
    print(f"\n{'Factor/Interaction':<30} {'Magnitude':>12} {'Percentage':>12}")
    print("-"*60)
    
    for r in results:
        percentage = (r['magnitude'] / total_effect_magnitude) * 100
        r['percentage'] = percentage
        if r['type'] == 'Main':
            print(f"{r['factor']:<30} {r['magnitude']:>12.6f} {percentage:>11.1f}%")
        else:
            print(f"{r['factor']:<30} {r['magnitude']:>12.6f} {percentage:>11.1f}%")
    
    return results

def fit_response_surface(df):
    """Fit quadratic response surface model"""
    print("\n" + "="*80)
    print("RESPONSE SURFACE MODEL (Quadratic)")
    print("="*80)
    
    # Center and scale factors for better numerical stability
    df['c_centered'] = df['c'] - df['c'].mean()
    df['k_centered'] = df['k_actual'] - df['k_actual'].mean()
    df['y_centered'] = df['y'] - df['y'].mean()
    
    # Quadratic model: linear + quadratic + interactions
    formula = ('emd ~ c_centered + k_centered + y_centered + '
               'I(c_centered**2) + I(k_centered**2) + I(y_centered**2) + '
               'c_centered:k_centered + c_centered:y_centered + k_centered:y_centered')
    
    model = ols(formula, data=df).fit()
    
    # Print coefficients
    print("\nModel Coefficients:")
    print("-"*60)
    coef_names = {
        'Intercept': 'Intercept',
        'c_centered': 'c (linear)',
        'k_centered': 'k (linear)',
        'y_centered': 'y (linear)',
        'I(c_centered ** 2)': 'c (quadratic)',
        'I(k_centered ** 2)': 'k (quadratic)',
        'I(y_centered ** 2)': 'y (quadratic)',
        'c_centered:k_centered': 'c × k',
        'c_centered:y_centered': 'c × y',
        'k_centered:y_centered': 'k × y'
    }
    
    for param, name in coef_names.items():
        coef = model.params[param]
        print(f"{name:<20} {coef:>12.6f}")
    
    # Model statistics
    print("\nModel Fit Statistics:")
    print("-"*60)
    print(f"R-squared:     {model.rsquared:.6f}")
    print(f"Adjusted R²:   {model.rsquared_adj:.6f}")
    print(f"RMSE:          {np.sqrt(model.mse_resid):.6f}")
    
    return model

def find_optimal_point(model, df):
    """Find optimal parameter combination using response surface"""
    print("\n" + "="*80)
    print("OPTIMAL PARAMETER COMBINATION (Response Surface)")
    print("="*80)
    
    # Create grid for optimization
    c_vals = np.linspace(df['c'].min(), df['c'].max(), 50)
    k_vals = np.linspace(df['k_actual'].min(), df['k_actual'].max(), 50)
    y_vals = np.linspace(df['y'].min(), df['y'].max(), 50)
    
    # Predict on grid (simplified - fix two factors at median while varying third)
    c_mean = df['c'].mean()
    k_mean = df['k_actual'].mean()
    y_mean = df['y'].mean()
    
    optimal = {'c': None, 'k': None, 'y': None, 'emd': np.inf}
    
    # Vary c
    for c in c_vals:
        pred_df = pd.DataFrame({
            'c_centered': [c - df['c'].mean()],
            'k_centered': [k_mean - df['k_actual'].mean()],
            'y_centered': [y_mean - df['y'].mean()]
        })
        pred = model.predict(pred_df)[0]
        if pred < optimal['emd']:
            optimal['emd'] = pred
            optimal['c'] = c
    
    # Vary k
    for k in k_vals:
        pred_df = pd.DataFrame({
            'c_centered': [optimal['c'] - df['c'].mean()],
            'k_centered': [k - df['k_actual'].mean()],
            'y_centered': [y_mean - df['y'].mean()]
        })
        pred = model.predict(pred_df)[0]
        if pred < optimal['emd']:
            optimal['emd'] = pred
            optimal['k'] = k
    
    # Vary y
    for y in y_vals:
        pred_df = pd.DataFrame({
            'c_centered': [optimal['c'] - df['c'].mean()],
            'k_centered': [optimal['k'] - df['k_actual'].mean()],
            'y_centered': [y - df['y'].mean()]
        })
        pred = model.predict(pred_df)[0]
        if pred < optimal['emd']:
            optimal['emd'] = pred
            optimal['y'] = y
    
    # Refine with local search
    for _ in range(3):
        for c in np.linspace(optimal['c'] - 50, optimal['c'] + 50, 10):
            for k in np.linspace(optimal['k'] - 0.02, optimal['k'] + 0.02, 10):
                for y in np.linspace(optimal['y'] - 5000, optimal['y'] + 5000, 10):
                    pred_df = pd.DataFrame({
                        'c_centered': [c - df['c'].mean()],
                        'k_centered': [k - df['k_actual'].mean()],
                        'y_centered': [y - df['y'].mean()]
                    })
                    pred = model.predict(pred_df)[0]
                    if pred < optimal['emd']:
                        optimal['emd'] = pred
                        optimal['c'] = c
                        optimal['k'] = k
                        optimal['y'] = y
    
    print(f"\nOptimal Cloud Base Height (c):  {optimal['c']:.0f} m")
    print(f"Optimal Core Ratio (k):          {optimal['k']:.3f}")
    print(f"Optimal Y-Distance (y):          {optimal['y']:.0f} m")
    print(f"Predicted Minimum EMD:           {optimal['emd']:.8f}")
    
    # Compare to actual best in data
    actual_best = df.loc[df['emd'].idxmin()]
    print(f"\nActual best EMD in data:         {actual_best['emd']:.8f}")
    print(f"Difference:                       {actual_best['emd'] - optimal['emd']:.8f}")
    
    return optimal

def create_rsm_plots(model, df, output_dir):
    """Create 3D response surface plots"""
    fig = plt.figure(figsize=(18, 6))
    
    # Get ranges
    c_range = np.linspace(df['c'].min(), df['c'].max(), 30)
    k_range = np.linspace(df['k_actual'].min(), df['k_actual'].max(), 30)
    y_range = np.linspace(df['y'].min(), df['y'].max(), 30)
    C, K = np.meshgrid(c_range, k_range)
    
    c_mean = df['c'].mean()
    k_mean = df['k_actual'].mean()
    y_mean = df['y'].mean()
    
    # Plot 1: c vs k (fix y at median)
    ax1 = fig.add_subplot(131, projection='3d')
    Z_ck = np.zeros_like(C)
    for i in range(len(c_range)):
        for j in range(len(k_range)):
            pred_df = pd.DataFrame({
                'c_centered': [c_range[i] - c_mean],
                'k_centered': [k_range[j] - k_mean],
                'y_centered': [y_mean - y_mean]
            })
            Z_ck[j, i] = model.predict(pred_df)[0]
    
    surf1 = ax1.plot_surface(C, K, Z_ck, cmap=cm.viridis, alpha=0.8)
    ax1.set_xlabel('Cloud Base Height (c) [m]')
    ax1.set_ylabel('Core Ratio (k)')
    ax1.set_zlabel('EMD')
    ax1.set_title('Response Surface: c × k\n(fixed y at median)')
    fig.colorbar(surf1, ax=ax1, shrink=0.5)
    
    # Plot 2: c vs y (fix k at median)
    ax2 = fig.add_subplot(132, projection='3d')
    C, Y = np.meshgrid(c_range, y_range)
    Z_cy = np.zeros_like(C)
    for i in range(len(c_range)):
        for j in range(len(y_range)):
            pred_df = pd.DataFrame({
                'c_centered': [c_range[i] - c_mean],
                'k_centered': [k_mean - k_mean],
                'y_centered': [y_range[j] - y_mean]
            })
            Z_cy[j, i] = model.predict(pred_df)[0]
    
    surf2 = ax2.plot_surface(C, Y, Z_cy, cmap=cm.plasma, alpha=0.8)
    ax2.set_xlabel('Cloud Base Height (c) [m]')
    ax2.set_ylabel('Y-Distance (y) [m]')
    ax2.set_zlabel('EMD')
    ax2.set_title('Response Surface: c × y\n(fixed k at median)')
    fig.colorbar(surf2, ax=ax2, shrink=0.5)
    
    # Plot 3: k vs y (fix c at median)
    ax3 = fig.add_subplot(133, projection='3d')
    K_grid, Y_grid = np.meshgrid(k_range, y_range)
    Z_ky = np.zeros_like(K_grid)
    for i in range(len(k_range)):
        for j in range(len(y_range)):
            pred_df = pd.DataFrame({
                'c_centered': [c_mean - c_mean],
                'k_centered': [k_range[i] - k_mean],
                'y_centered': [y_range[j] - y_mean]
            })
            Z_ky[j, i] = model.predict(pred_df)[0]
    
    surf3 = ax3.plot_surface(K_grid, Y_grid, Z_ky, cmap=cm.inferno, alpha=0.8)
    ax3.set_xlabel('Core Ratio (k)')
    ax3.set_ylabel('Y-Distance (y) [m]')
    ax3.set_zlabel('EMD')
    ax3.set_title('Response Surface: k × y\n(fixed c at median)')
    fig.colorbar(surf3, ax=ax3, shrink=0.5)
    
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'rsm_3d_surfaces.png'), dpi=150)
    print(f"\n✓ 3D response surfaces saved to: {output_dir}/rsm_3d_surfaces.png")
    plt.close()
    
    # Create contour plots
    fig, axes = plt.subplots(1, 3, figsize=(15, 5))
    
    # Contour: c vs k
    contour1 = axes[0].contour(C, K, Z_ck, levels=20, cmap='viridis')
    axes[0].clabel(contour1, inline=True, fontsize=8)
    axes[0].set_xlabel('Cloud Base Height (c) [m]')
    axes[0].set_ylabel('Core Ratio (k)')
    axes[0].set_title('Contour: c × k')
    
    # Contour: c vs y
    contour2 = axes[1].contour(C, Y, Z_cy, levels=20, cmap='plasma')
    axes[1].clabel(contour2, inline=True, fontsize=8)
    axes[1].set_xlabel('Cloud Base Height (c) [m]')
    axes[1].set_ylabel('Y-Distance (y) [m]')
    axes[1].set_title('Contour: c × y')
    
    # Contour: k vs y
    contour3 = axes[2].contour(K_grid, Y_grid, Z_ky, levels=20, cmap='inferno')
    axes[2].clabel(contour3, inline=True, fontsize=8)
    axes[2].set_xlabel('Core Ratio (k)')
    axes[2].set_ylabel('Y-Distance (y) [m]')
    axes[2].set_title('Contour: k × y')
    
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'rsm_contours.png'), dpi=150)
    print(f"✓ Contour plots saved to: {output_dir}/rsm_contours.png")
    plt.close()

def main_effects_plot_rsm(df, output_dir):
    """Create main effects plot"""
    fig, axes = plt.subplots(1, 3, figsize=(15, 5))
    
    factors = [('c', 'Cloud Base Height (m)', 'c'), 
               ('k_actual', 'Core Ratio (k)', 'k'), 
               ('y', 'Y-Distance (m)', 'y')]
    
    for idx, (factor, title, label) in enumerate(factors):
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
        ax.set_title(f'Main Effect: {label}')
        ax.grid(True, alpha=0.3)
        
        # Add value labels
        for i, (x, y) in enumerate(zip(means.index, means.values)):
            if factor == 'k_actual':
                ax.annotate(f'{y:.4f}', (x_pos[i], y), xytext=(0, 10), 
                           textcoords='offset points', ha='center', fontsize=9)
            else:
                ax.annotate(f'{y:.4f}', (x, y), xytext=(0, 10), 
                           textcoords='offset points', ha='center', fontsize=9)
    
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'main_effects_rsm.png'), dpi=150)
    print(f"✓ Main effects plot saved to: {output_dir}/main_effects_rsm.png")
    plt.close()

def save_summary_to_file(df, model, effects, optimal, output_dir):
    """Save summary statistics to a text file"""
    summary_file = os.path.join(output_dir, 'analysis_summary.txt')
    
    with open(summary_file, 'w') as f:
        f.write("="*80 + "\n")
        f.write("RESPONSE SURFACE METHODOLOGY (RSM) & EFFECTS ANALYSIS\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("="*80 + "\n\n")
        
        f.write(f"Data loaded: {len(df)} runs\n")
        f.write(f"EMD range: {df['emd'].min():.8f} - {df['emd'].max():.8f}\n")
        f.write(f"EMD mean: {df['emd'].mean():.8f} ± {df['emd'].std():.8f}\n\n")
        
        f.write("="*80 + "\n")
        f.write("MODEL COEFFICIENTS\n")
        f.write("="*80 + "\n")
        coef_names = {
            'Intercept': 'Intercept',
            'c_centered': 'c (linear)',
            'k_centered': 'k (linear)',
            'y_centered': 'y (linear)',
            'I(c_centered ** 2)': 'c (quadratic)',
            'I(k_centered ** 2)': 'k (quadratic)',
            'I(y_centered ** 2)': 'y (quadratic)',
            'c_centered:k_centered': 'c × k',
            'c_centered:y_centered': 'c × y',
            'k_centered:y_centered': 'k × y'
        }
        for param, name in coef_names.items():
            coef = model.params[param]
            f.write(f"{name:<20} {coef:>12.6f}\n")
        
        f.write("\n" + "="*80 + "\n")
        f.write("MODEL FIT STATISTICS\n")
        f.write("="*80 + "\n")
        f.write(f"R-squared:     {model.rsquared:.6f}\n")
        f.write(f"Adjusted R²:   {model.rsquared_adj:.6f}\n")
        f.write(f"RMSE:          {np.sqrt(model.mse_resid):.6f}\n\n")
        
        f.write("="*80 + "\n")
        f.write("OPTIMAL PARAMETER COMBINATION\n")
        f.write("="*80 + "\n")
        f.write(f"Cloud Base Height (c):  {optimal['c']:.0f} m\n")
        f.write(f"Core Ratio (k):          {optimal['k']:.3f}\n")
        f.write(f"Y-Distance (y):          {optimal['y']:.0f} m\n")
        f.write(f"Predicted Minimum EMD:   {optimal['emd']:.8f}\n\n")
        
        actual_best = df.loc[df['emd'].idxmin()]
        f.write(f"Actual best EMD in data: {actual_best['emd']:.8f}\n")
        f.write(f"Difference:              {actual_best['emd'] - optimal['emd']:.8f}\n\n")
        
        # Save effects summary
        f.write("="*80 + "\n")
        f.write("EFFECTS RANKING\n")
        f.write("="*80 + "\n")
        sorted_effects = sorted(effects, key=lambda x: x['percentage'], reverse=True)
        for i, effect in enumerate(sorted_effects, 1):
            if effect['type'] == 'Main':
                f.write(f"{i}. {effect['factor']}: {effect['percentage']:.1f}% (effect={effect['effect']:+.6f})\n")
            else:
                f.write(f"{i}. {effect['factor']}: {effect['percentage']:.1f}%\n")
    
    print(f"✓ Summary saved to: {output_dir}/analysis_summary.txt")

def main():
    if len(sys.argv) != 2:
        print("Usage: python3 rsm_analysis.py <emd_results_file>")
        print("Example: python3 rsm_analysis.py batch_test_20260506_155323/emd_results.txt")
        sys.exit(1)
    
    filepath = sys.argv[1]
    
    # Get the batch folder from the filepath
    batch_folder = os.path.dirname(filepath)
    if not batch_folder:
        batch_folder = os.getcwd()
    
    # Set up output redirection
    output_log = os.path.join(batch_folder, 'analysis_output.txt')
    tee = Tee(output_log)
    sys.stdout = tee
    
    print("="*80)
    print("RESPONSE SURFACE METHODOLOGY (RSM) & EFFECTS ANALYSIS")
    print("For Computer Experiments with Noise")
    print("="*80)
    print(f"\nInput file: {filepath}")
    print(f"Output directory: {batch_folder}")
    print(f"Log file: {output_log}")
    
    # Read data
    df = read_emd_results(filepath)
    print(f"\nData loaded: {len(df)} runs")
    print(f"EMD range: {df['emd'].min():.8f} - {df['emd'].max():.8f}")
    
    # Effects analysis
    effects = effects_analysis(df)
    
    # Fit response surface
    model = fit_response_surface(df)
    
    # Find optimal point
    optimal = find_optimal_point(model, df)
    
    # Create visualizations
    print("\n" + "="*80)
    print("GENERATING VISUALIZATIONS")
    print("="*80)
    main_effects_plot_rsm(df, batch_folder)
    create_rsm_plots(model, df, batch_folder)
    
    # Save summary
    save_summary_to_file(df, model, effects, optimal, batch_folder)
    
    # Final summary
    print("\n" + "="*80)
    print("SUMMARY: MOST INFLUENTIAL FACTORS")
    print("="*80)
    
    # Sort effects by percentage
    sorted_effects = sorted(effects, key=lambda x: x['percentage'], reverse=True)
    print("\nRanked by contribution to total effect magnitude:")
    for i, effect in enumerate(sorted_effects[:5], 1):
        if effect['type'] == 'Main':
            print(f"  {i}. {effect['factor']}: {effect['percentage']:.1f}% (effect={effect['effect']:+.6f})")
        else:
            print(f"  {i}. {effect['factor']}: {effect['percentage']:.1f}%")
    
    print("\n" + "="*80)
    print("✅ ANALYSIS COMPLETE")
    print(f"All outputs saved to: {batch_folder}")
    print("  - analysis_output.txt (console output)")
    print("  - analysis_summary.txt (summary statistics)")
    print("  - main_effects_rsm.png")
    print("  - rsm_3d_surfaces.png")
    print("  - rsm_contours.png")
    print("="*80)
    
    # Restore stdout
    sys.stdout = tee.terminal

if __name__ == "__main__":
    main()
