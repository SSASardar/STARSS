"""
visualize_rainfall_discrepancy.py
Visualizes the difference between regular stats and AD stats discrepancies.
Four key plots: scatter, histogram, Q-Q plot, and boxplot comparison.
Each visualization is saved as a separate figure.
Uses the centralized stylesheet for consistent PhD thesis styling.
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
file_path = 'batch_test_20260827_113654/results_sums.txt'  # Change this to your actual file path

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
ax1.set_xlabel('Stats Discrepancy')
ax1.set_ylabel('AD Stats Discrepancy')
ax1.set_title('Scatter Plot: Stats vs AD Stats')
ax1.legend(loc='best')
ax1.grid(True, alpha=0.3)
ax1.set_aspect('equal', adjustable='box')

plt.tight_layout()
plt.savefig('figures/cs_scatter_plot.png', dpi=300, bbox_inches='tight')
plt.savefig('figures/cs_scatter_plot.pdf', bbox_inches='tight')
plt.close()
print("Figure 1 saved: scatter_plot")

# ---- Figure 2: Histogram of differences ----
fig2, ax2 = plt.subplots(figsize=(5.5, 4.0))

# Histogram
ax2.hist(df['Difference'], bins=15, edgecolor='white', linewidth=0.8,
         color=stylesheet.COLORS['blue'], alpha=0.7)

# Add reference lines
ax2.axvline(0, color='black', linestyle='-', linewidth=1.5, alpha=0.7)

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

# ---- Figure 3: Q-Q plot for normality check ----
fig3, ax3 = plt.subplots(figsize=(5.5, 4.0))

# Q-Q plot
stats.probplot(df['Difference'], dist="norm", plot=ax3)

# Customize colors and styles
ax3.get_lines()[0].set_color(stylesheet.COLORS['blue'])  # Data points
ax3.get_lines()[0].set_marker('o')
ax3.get_lines()[0].set_markersize(4)
ax3.get_lines()[0].set_alpha(0.6)
ax3.get_lines()[1].set_color(stylesheet.COLORS['red'])   # Reference line
ax3.get_lines()[1].set_linestyle('--')
ax3.get_lines()[1].set_linewidth(1.5)

# Labels and formatting
ax3.set_xlabel('Theoretical Quantiles')
ax3.set_ylabel('Sample Quantiles')
ax3.set_title('Q-Q Plot: Normality Check')
ax3.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('figures/cs_qq_plot.png', dpi=300, bbox_inches='tight')
plt.savefig('figures/cs_qq_plot.pdf', bbox_inches='tight')
plt.close()
print("Figure 3 saved: qq_plot")

# ---- Figure 4: Boxplot comparison ----
fig4, ax4 = plt.subplots(figsize=(5.5, 4.0))

# Prepare data for boxplot
data_to_plot = [df['Stats_Discrepancy'].values, df['AD_Stats_Discrepancy'].values]
bp = ax4.boxplot(data_to_plot, patch_artist=True, 
                 tick_labels=['Stats', 'AD Stats'],
                 showmeans=False)  # Turned off means to avoid errors

# Color the boxes
bp['boxes'][0].set_facecolor(stylesheet.COLORS['blue'])
bp['boxes'][1].set_facecolor(stylesheet.COLORS['orange'])
bp['boxes'][0].set_alpha(0.7)
bp['boxes'][1].set_alpha(0.7)
bp['boxes'][0].set_edgecolor('black')
bp['boxes'][1].set_edgecolor('black')
bp['boxes'][0].set_linewidth(0.8)
bp['boxes'][1].set_linewidth(0.8)

# Style the median lines
bp['medians'][0].set_color('black')
bp['medians'][0].set_linewidth(2)
bp['medians'][1].set_color('black')
bp['medians'][1].set_linewidth(2)

# Style the whiskers and caps
for whisker in bp['whiskers']:
    whisker.set_color('black')
for cap in bp['caps']:
    cap.set_color('black')
for flier in bp['fliers']:
    flier.set_marker('o')
    flier.set_markersize(4)
    flier.set_alpha(0.5)

# Labels and formatting
ax4.set_ylabel('Discrepancy Value')
ax4.set_title('Boxplot Comparison: Stats vs AD Stats')
ax4.grid(True, alpha=0.3, axis='y')

plt.tight_layout()
plt.savefig('figures/cs_boxplot_comparison.png', dpi=300, bbox_inches='tight')
plt.savefig('figures/cs_boxplot_comparison.pdf', bbox_inches='tight')
plt.close()
print("Figure 4 saved: boxplot_comparison")

print("\nAll four figures have been generated successfully!")
print("Files saved in 'figures/' directory:")
print("  - figures/cs_1scatter_plot.png/pdf")
print("  - figures/cs_1histogram_differences.png/pdf")
print("  - figures/cs_1qq_plot.png/pdf")
print("  - figures/cs_1boxplot_comparison.png/pdf")
