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
# 1.5 OUTPUT PARAMETER COMBINATIONS WITH NEGATIVE DIFFERENCES
# ============================================================

# Filter rows where Difference < 0 (AD performs better - lower discrepancy)
negative_diff_df = df[df['Difference'] < 0].copy()

# Sort by difference (most negative first) to see largest discrepancies
negative_diff_df_sorted = negative_diff_df.sort_values('Difference', ascending=True)

print(f"\n{'='*60}")
print(f"PARAMETER COMBINATIONS WHERE AD PERFORMS BETTER (Difference < 0)")
print(f"{'='*60}")
print(f"Total number of cases with Difference < 0: {len(negative_diff_df)}")
print(f"Percentage of total samples: {len(negative_diff_df)/n*100:.2f}%\n")

# Print all parameter combinations with their differences
print("Parameter combinations (x1-x7) with Difference < 0 (sorted by most negative first):")
print("-" * 80)
print(f"{'x1':>8} {'x2':>8} {'x3':>8} {'x4':>8} {'x5':>8} {'x6':>8} {'x7':>8} {'Difference':>12} {'Stats_Discrep':>14} {'AD_Discrep':>14}")
print("-" * 80)

# Print all rows with negative difference
for idx, row in negative_diff_df_sorted.iterrows():
    print(f"{row['x1']:8.2f} {row['x2']:8.2f} {row['x3']:8.2f} {row['x4']:8.2f} "
          f"{row['x5']:8.2f} {row['x6']:8.2f} {row['x7']:8.2f} "
          f"{row['Difference']:12.6f} {row['Stats_Discrepancy']:14.6f} {row['AD_Stats_Discrepancy']:14.6f}")

# Also save to CSV file for further analysis
negative_diff_df_sorted.to_csv('figures/cs_better_performance_of_adaptive.csv', index=False)
print(f"\nNegative difference cases saved to: figures/cs_better_performance_of_adaptive.csv")

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

# ---- Figure 2: Histogram of differences with colored shading ----
fig2, ax2 = plt.subplots(figsize=(5.5, 4.0))

# Create histogram
counts, bins, patches = ax2.hist(df['Difference'], bins=30, edgecolor='white', 
                                 linewidth=0.8, alpha=0.7)

# Color bars based on whether they're positive or negative
for count, patch in zip(counts, patches):
    # Get the center of the bin
    bin_center = patch.get_x() + patch.get_width() / 2
    if bin_center < 0:
        patch.set_facecolor(stylesheet.COLORS['green'])  # Green for negative (AD better)
    else:
        patch.set_facecolor(stylesheet.COLORS['red'])    # Red for positive (Stats better)

# Add reference lines
ax2.axvline(0, color='black', linestyle='-', linewidth=1.5, alpha=0.7)
ax2.axvline(df['Difference'].mean(), color='blue', linestyle='--', linewidth=1.5, 
            alpha=0.7, label=f'Mean: {df["Difference"].mean():.4f}')

# Add text annotations showing counts
neg_count = len(df[df['Difference'] < 0])
pos_count = len(df[df['Difference'] > 0])
zero_count = len(df[df['Difference'] == 0])

# Add annotation box
#textstr = f'AD better (neg): {neg_count} ({neg_count/n*100:.1f}%)\nStats better (pos): {pos_count} ({pos_count/n*100:.1f}%)'
#props = dict(boxstyle='round', facecolor='white', alpha=0.8)
#ax2.text(0.98, 0.95, textstr, transform=ax2.transAxes, fontsize=8,
#         verticalalignment='top', horizontalalignment='right', bbox=props)

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
print("  - figures/cs_scatter_plot.png/pdf")
print("  - figures/cs_histogram_differences.png/pdf")
print("  - figures/cs_better_performance_of_adaptive.csv")
