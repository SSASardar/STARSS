"""
visualize_rainfall_discrepancy.py
Visualizes the difference between regular stats and AD stats discrepancies.
Four key plots: scatter, histogram, Q-Q plot, and boxplot comparison.
Each visualization is saved as a separate figure.
Uses the centralized stylesheet for consistent PhD thesis styling.
Includes t-test and saves results to a text file.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy import stats
import stylesheet  # Your centralized stylesheet
import os
from datetime import datetime

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

# Calculate absolute difference
df['Difference'] = np.abs(df['Stats_Discrepancy'] - df['AD_Stats_Discrepancy'])

n = len(df)

# ============================================================
# 2. PERFORM T-TEST
# ============================================================

# Paired t-test (since these are paired measurements)
t_stat, p_value = stats.ttest_rel(df['Stats_Discrepancy'], df['AD_Stats_Discrepancy'])

# Also perform independent t-test for comparison
t_stat_ind, p_value_ind = stats.ttest_ind(df['Stats_Discrepancy'], df['AD_Stats_Discrepancy'])

# Calculate summary statistics
stats_mean = df['Stats_Discrepancy'].mean()
stats_std = df['Stats_Discrepancy'].std()
stats_median = df['Stats_Discrepancy'].median()
stats_min = df['Stats_Discrepancy'].min()
stats_max = df['Stats_Discrepancy'].max()

ad_stats_mean = df['AD_Stats_Discrepancy'].mean()
ad_stats_std = df['AD_Stats_Discrepancy'].std()
ad_stats_median = df['AD_Stats_Discrepancy'].median()
ad_stats_min = df['AD_Stats_Discrepancy'].min()
ad_stats_max = df['AD_Stats_Discrepancy'].max()

diff_mean = df['Difference'].mean()
diff_std = df['Difference'].std()
diff_median = df['Difference'].median()
diff_min = df['Difference'].min()
diff_max = df['Difference'].max()



# ============================================================
# 2.5 CALCULATE EFFECT SIZE AND PRACTICAL SIGNIFICANCE
# ============================================================

# Calculate Cohen's d (effect size)
cohens_d = (stats_mean - ad_stats_mean) / np.sqrt((stats_std**2 + ad_stats_std**2)/2)

# Calculate percentage improvement
pct_improvement = (stats_mean - ad_stats_mean) / stats_mean * 100

# Print to console
print(f"\nEffect Size (Cohen's d): {cohens_d:.3f}")
print(f"Percentage Improvement: {pct_improvement:.2f}%")




# ============================================================
# 3. SAVE T-TEST RESULTS TO TXT FILE
# ============================================================

with open('figures/cs_t-test.txt', 'w') as f:
    f.write("=" * 80 + "\n")
    f.write("T-TEST RESULTS: Stats_Discrepancy vs AD_Stats_Discrepancy\n")
    f.write("=" * 80 + "\n\n")
    
    f.write(f"Date and Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    f.write(f"Number of samples: {n}\n\n")
    
    f.write("-" * 80 + "\n")
    f.write("SUMMARY STATISTICS\n")
    f.write("-" * 80 + "\n\n")
    
    f.write("Stats_Discrepancy:\n")
    f.write(f"  Mean:     {stats_mean:.6f}\n")
    f.write(f"  Std Dev:  {stats_std:.6f}\n")
    f.write(f"  Median:   {stats_median:.6f}\n")
    f.write(f"  Min:      {stats_min:.6f}\n")
    f.write(f"  Max:      {stats_max:.6f}\n\n")
    
    f.write("AD_Stats_Discrepancy:\n")
    f.write(f"  Mean:     {ad_stats_mean:.6f}\n")
    f.write(f"  Std Dev:  {ad_stats_std:.6f}\n")
    f.write(f"  Median:   {ad_stats_median:.6f}\n")
    f.write(f"  Min:      {ad_stats_min:.6f}\n")
    f.write(f"  Max:      {ad_stats_max:.6f}\n\n")
    
    f.write("Absolute Difference (|Stats - AD|):\n")
    f.write(f"  Mean:     {diff_mean:.6f}\n")
    f.write(f"  Std Dev:  {diff_std:.6f}\n")
    f.write(f"  Median:   {diff_median:.6f}\n")
    f.write(f"  Min:      {diff_min:.6f}\n")
    f.write(f"  Max:      {diff_max:.6f}\n\n")
    
    f.write("-" * 80 + "\n")
    f.write("PAIRED T-TEST (Recommended for paired data)\n")
    f.write("-" * 80 + "\n\n")
    f.write(f"t-statistic: {t_stat:.6f}\n")
    f.write(f"p-value:     {p_value:.6e}\n")
    f.write(f"Degrees of freedom: {n - 1}\n\n")
    
    # Interpret the p-value
    if p_value < 0.001:
        significance = "p < 0.001 (Highly significant)"
    elif p_value < 0.01:
        significance = "p < 0.01 (Very significant)"
    elif p_value < 0.05:
        significance = "p < 0.05 (Significant)"
    elif p_value < 0.1:
        significance = "p < 0.1 (Marginally significant)"
    else:
        significance = "p >= 0.1 (Not significant)"
    
    f.write(f"Interpretation: {significance}\n\n")
    
    f.write("-" * 80 + "\n")
    f.write("INDEPENDENT T-TEST (For reference)\n")
    f.write("-" * 80 + "\n\n")
    f.write(f"t-statistic: {t_stat_ind:.6f}\n")
    f.write(f"p-value:     {p_value_ind:.6e}\n\n")
    
    f.write("-" * 80 + "\n")
    f.write("HYPOTHESIS TESTING\n")
    f.write("-" * 80 + "\n\n")
    f.write("Null Hypothesis (H0): The mean of Stats_Discrepancy equals the mean of AD_Stats_Discrepancy\n")
    f.write("Alternative Hypothesis (H1): The means are significantly different\n\n")
    
    if p_value < 0.05:
        f.write("CONCLUSION: Reject the null hypothesis. ")
        f.write("There is a statistically significant difference between the two discrepancy measures.\n")
    else:
        f.write("CONCLUSION: Fail to reject the null hypothesis. ")
        f.write("There is no statistically significant difference between the two discrepancy measures.\n")
    
    f.write("\n" + "=" * 80 + "\n")
    f.write("END OF REPORT\n")
    f.write("=" * 80 + "\n")

print("T-test results saved to: figures/cs_t-test.txt")

# Also print to console for immediate viewing
print("\n" + "=" * 50)
print("T-TEST SUMMARY")
print("=" * 50)
print(f"Paired t-test: t = {t_stat:.4f}, p = {p_value:.6e}")
print(f"Interpretation: {'Significant' if p_value < 0.05 else 'Not significant'}")
print("=" * 50 + "\n")

# ============================================================
# 4. CREATE INDIVIDUAL FIGURES
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
ax2.set_xlabel('Absolute Difference (|Stats - AD|)')
ax2.set_ylabel('Frequency')
ax2.set_title('Distribution of Absolute Differences')
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
print("  - figures/cs_scatter_plot.png/pdf")
print("  - figures/cs_histogram_differences.png/pdf")
print("  - figures/cs_qq_plot.png/pdf")
print("  - figures/cs_boxplot_comparison.png/pdf")
print("  - figures/cs_t-test.txt")
