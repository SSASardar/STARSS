"""
visualize_rainfall_discrepancy.py
Visualizes the difference between regular stats and AD stats discrepancies.
Two key plots: scatter and histogram of non-absolute differences.
Each visualization is saved as a separate figure.
Uses the centralized stylesheet for consistent PhD thesis styling.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import stylesheet  # Your centralized stylesheet
import os

# ============================================================
# 1. LOAD AND PREPARE DATA
# ============================================================

# Create figures directory if it doesn't exist
os.makedirs('figures', exist_ok=True)

# Read the data - UPDATE THIS PATH TO YOUR ACTUAL FILE
file_path = 'batch_test_20260831_111605/results_sums.txt'  # Change this to your actual file path

# Try reading with different methods
try:
    # Method 1: Using sep='\\s+' with raw string to avoid escape warning
    df = pd.read_csv(file_path, comment='#', sep=r'\s+',
                     header=None,
                     names=['x1', 'x2', 'x3', 'x4', 'x5', 'x6', 'x7',
                            'Stats_Discrepancy', 'AD_Stats_Discrepancy'])
except:
    # Method 2: Manual parsing for .txt files
    with open(file_path, 'r') as f:
        lines = f.readlines()
    
    # Skip comment lines (starting with #)
    data_lines = []
    for line in lines:
        if not line.startswith('#'):
            data_lines.append(line.strip().split())
    
    # Convert to DataFrame
    df = pd.DataFrame(data_lines, columns=['x1', 'x2', 'x3', 'x4', 'x5', 'x6', 'x7',
                                           'Stats_Discrepancy', 'AD_Stats_Discrepancy'])
    # Convert all columns to numeric
    df = df.apply(pd.to_numeric)

# Calculate non-absolute difference (Stats - AD)
df['Difference'] = df['Stats_Discrepancy'] - df['AD_Stats_Discrepancy']

n = len(df)

# Print summary statistics to console
print(f"Number of samples: {n}")
print(f"\nDifference (Stats - AD) Summary:")
print(f"  Mean:     {df['Difference'].mean():.6f}")
print(f"  Std Dev:  {df['Difference'].std():.6f}")
print(f"  Min:      {df['Difference'].min():.6f}")
print(f"  Max:      {df['Difference'].max():.6f}")
print(f"  Median:   {df['Difference'].median():.6f}")

# ============================================================
# 2. CREATE INDIVIDUAL FIGURES
# ============================================================

# ---- Figure 1: Scatter plot: Stats vs AD ----
fig1, ax1 = plt.subplots(figsize=(5.5, 4.0))

# Scatter points
ax1.scatter(df['Stats_Discrepancy'], df['AD_Stats_Discrepancy'], 
            alpha=0.6, s=30, color=stylesheet.COLORS['blue'], 
            edgecolors='white', linewidth=0.5)

# Add 1:1 line
min_val = min(df['Stats_Discrepancy'].min(), df['AD_Stats_Discrepancy'].min())
max_val = max(df['Stats_Discrepancy'].max(), df['AD_Stats_Discrepancy'].max())
ax1.plot([min_val, max_val], [min_val, max_val], 'k--', alpha=0.5, 
         linewidth=1.5)

# Labels and formatting
ax1.set_xlabel('Stats Discrepancy (1 Radar)')
ax1.set_ylabel('AD Stats Discrepancy (2 Radars)')
ax1.set_title('Scatter Plot: 1 Radar vs 2 Radars')
ax1.grid(True, alpha=0.3)
ax1.set_aspect('equal', adjustable='box')

plt.tight_layout()
plt.savefig('figures/cs_scatter_plot.png', dpi=300, bbox_inches='tight')
plt.savefig('figures/cs_scatter_plot.pdf', bbox_inches='tight')
plt.close()
print("\nFigure 1 saved: scatter_plot")

# ---- Figure 2: Histogram of differences ----
fig2, ax2 = plt.subplots(figsize=(5.5, 4.0))

# Histogram of non-absolute differences
ax2.hist(df['Difference'], bins=30, edgecolor='white', linewidth=0.8,
         color=stylesheet.COLORS['blue'], alpha=0.7)

# Add reference lines
ax2.axvline(0, color='black', linestyle='-', linewidth=1.5, alpha=0.7, label='Zero Difference')
ax2.axvline(df['Difference'].mean(), color='red', linestyle='--', linewidth=1.5, 
            alpha=0.7, label=f'Mean: {df["Difference"].mean():.4f}')

# Labels and formatting
ax2.set_xlabel('Difference (1 Radar - 2 Radars) [mm per hour]')
ax2.set_ylabel('Frequency')
ax2.set_title('Distribution of Differences in Rainfall Depth')
ax2.legend(loc='best')
ax2.grid(True, alpha=0.3, axis='y')

plt.tight_layout()
plt.savefig('figures/cs_histogram_differences.png', dpi=300, bbox_inches='tight')
plt.savefig('figures/cs_histogram_differences.pdf', bbox_inches='tight')
plt.close()
print("Figure 2 saved: histogram_differences")

print("\nBoth figures have been generated successfully!")
print("Files saved in 'figures/' directory:")
print("  - figures/scatter_plot.png/pdf")
print("  - figures/histogram_differences.png/pdf")
