"""
visualize_rainfall_discrepancy.py
Visualizes the difference between regular stats and AD stats discrepancies.
Two key plots: scatter and histogram.
Each visualization is saved as a separate figure.
Uses the centralized stylesheet for consistent PhD thesis styling.
Additionally, exports parameter combinations where Difference < 0.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy import stats
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

# Calculate difference
df['Difference'] = df['Stats_Discrepancy'] - df['AD_Stats_Discrepancy']

n = len(df)

# ============================================================
# 2. EXTRACT PARAMETER COMBINATIONS WHERE DIFFERENCE < 0
# ============================================================

# Filter rows where Difference is less than 0
negative_diff_df = df[df['Difference'] < 0]

# Get the parameter combinations (x1 through x7) for these rows
negative_params = negative_diff_df[['x1', 'x2', 'x3', 'x4', 'x5', 'x6', 'x7']].copy()

# Add the difference and discrepancy values for reference
negative_params['Difference'] = negative_diff_df['Difference']
negative_params['Stats_Discrepancy'] = negative_diff_df['Stats_Discrepancy']
negative_params['AD_Stats_Discrepancy'] = negative_diff_df['AD_Stats_Discrepancy']

# Save to CSV
negative_params.to_csv('figures/negative_difference_parameters.csv', index=False)
print(f"Found {len(negative_params)} parameter combinations with Difference < 0")
print("Saved to: figures/cs_negative_difference_parameters.csv")

# Also print a summary to console
print("\nFirst 10 parameter combinations with Difference < 0:")
print(negative_params.head(10).to_string())

# ============================================================
# 3. CREATE INDIVIDUAL FIGURES
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
ax1.set_xlabel('Stats Discrepancy')
ax1.set_ylabel('AD Stats Discrepancy')
ax1.set_title('Scatter Plot: Stats vs AD Stats')
ax1.grid(True, alpha=0.3)
ax1.set_aspect('equal', adjustable='box')

plt.tight_layout()
plt.savefig('figures/cs_scatter_plot.png', dpi=300, bbox_inches='tight')
plt.savefig('figures/cs_scatter_plot.pdf', bbox_inches='tight')
plt.close()
print("\nFigure 1 saved: scatter_plot")

# ---- Figure 2: Histogram of differences ----
fig2, ax2 = plt.subplots(figsize=(5.5, 4.0))

# Histogram
ax2.hist(df['Difference'], bins=15, edgecolor='white', linewidth=0.8,
         color=stylesheet.COLORS['blue'], alpha=0.7)

# Add reference lines
ax2.axvline(0, color='black', linestyle='-', linewidth=1.5, alpha=0.7)

# Add a vertical line at the mean if desired
mean_diff = df['Difference'].mean()
ax2.axvline(mean_diff, color='red', linestyle='--', linewidth=1.5, alpha=0.7, 
            label=f'Mean: {mean_diff:.4f}')

# Labels and formatting
ax2.set_xlabel('Difference (Stats - AD)')
ax2.set_ylabel('Frequency')
ax2.set_title('Distribution of Differences')
ax2.legend(loc='best')
ax2.grid(True, alpha=0.3, axis='y')

plt.tight_layout()
plt.savefig('figures/cs_histogram_differences.png', dpi=300, bbox_inches='tight')
plt.savefig('figures/cs_histogram_differences.pdf', bbox_inches='tight')
plt.close()
print("Figure 2 saved: histogram_differences")

print("\nAll figures have been generated successfully!")
print("Files saved in 'figures/' directory:")
print("  - figures/scatter_plot.png/pdf")
print("  - figures/histogram_differences.png/pdf")
print("  - figures/negative_difference_parameters.csv (parameter list)")
