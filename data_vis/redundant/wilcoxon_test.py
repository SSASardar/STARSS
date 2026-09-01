"""
wilcoxon_test.py
Wilcoxon signed-rank test for comparing Stats vs AD Stats strategies.
Non-parametric test for paired data.
"""

import pandas as pd
import numpy as np
from scipy.stats import wilcoxon, ranksums

# ============================================================
# 1. LOAD DATA
# ============================================================

print("=" * 60)
print("WILCOXON SIGNED-RANK TEST")
print("Stats vs AD Stats Strategy Comparison")
print("=" * 60)

# Read the data
df = pd.read_csv('batch_test_20260831_111605/results_sums.txt', comment='#', sep=r'\s+',
                 header=None,
                 names=['x1', 'x2', 'x3', 'x4', 'x5', 'x6', 'x7',
                        'Stats_Discrepancy', 'AD_Stats_Discrepancy'])

# Calculate difference
df['Difference'] = df['Stats_Discrepancy'] - df['AD_Stats_Discrepancy']

n = len(df)
print(f"\nSample size: {n:,}")

# ============================================================
# 2. DESCRIPTIVE STATISTICS
# ============================================================

print("\n" + "-" * 60)
print("DESCRIPTIVE STATISTICS")
print("-" * 60)

# Count positive/negative
n_pos = (df['Difference'] > 0).sum()
n_neg = (df['Difference'] < 0).sum()
n_zero = (df['Difference'] == 0).sum()

print(f"\nDifference direction:")
print(f"  Positive (Stats > AD): {n_pos:,} ({n_pos/n*100:.1f}%)")
print(f"  Negative (Stats < AD): {n_neg:,} ({n_neg/n*100:.1f}%)")
print(f"  Zero: {n_zero:,} ({n_zero/n*100:.1f}%)")

print(f"\nDifference statistics:")
print(f"  Mean: {df['Difference'].mean():.6f}")
print(f"  Median: {df['Difference'].median():.6f}")
print(f"  Std Dev: {df['Difference'].std():.6f}")
print(f"  Min: {df['Difference'].min():.6f}")
print(f"  Max: {df['Difference'].max():.6f}")

# ============================================================
# 3. WILCOXON SIGNED-RANK TEST
# ============================================================

print("\n" + "-" * 60)
print("WILCOXON SIGNED-RANK TEST")
print("-" * 60)
print("Null hypothesis: Median difference = 0")
print("Alternative: Median difference ≠ 0")
print("Assumption: Symmetric differences (no normality required)")

# Perform Wilcoxon signed-rank test
w_stat, p_value = wilcoxon(df['Stats_Discrepancy'], df['AD_Stats_Discrepancy'])

print(f"\nResults:")
print(f"  W-statistic: {w_stat:.1f}")
print(f"  p-value: {p_value:.6e}")

# Calculate effect size (r = z / sqrt(n))
z_stat, _ = ranksums(df['Stats_Discrepancy'], df['AD_Stats_Discrepancy'])
r_effect = abs(z_stat) / np.sqrt(n)

print(f"\nEffect size (r): {r_effect:.6f}")
if r_effect < 0.1:
    print(f"  → Negligible effect")
elif r_effect < 0.3:
    print(f"  → Small effect")
elif r_effect < 0.5:
    print(f"  → Medium effect")
else:
    print(f"  → Large effect")

# ============================================================
# 4. SIGNIFICANCE AT DIFFERENT LEVELS
# ============================================================

print("\n" + "-" * 60)
print("SIGNIFICANCE")
print("-" * 60)

print(f"\nSignificance at different α levels:")
for alpha in [0.001, 0.01, 0.05]:
    if p_value < alpha:
        print(f"  ✓ p < {alpha}: SIGNIFICANT")
    else:
        print(f"  ✗ p < {alpha}: NOT significant")

# ============================================================
# 5. INTERPRETATION
# ============================================================

print("\n" + "=" * 60)
print("INTERPRETATION")
print("=" * 60)

if p_value < 0.001:
    print("\n✓ STATISTICALLY SIGNIFICANT at α=0.001")
elif p_value < 0.01:
    print("\n✓ STATISTICALLY SIGNIFICANT at α=0.01")
elif p_value < 0.05:
    print("\n✓ STATISTICALLY SIGNIFICANT at α=0.05")
else:
    print("\n✗ NOT STATISTICALLY SIGNIFICANT at α=0.05")

if df['Difference'].mean() > 0:
    print(f"\nDirection: Stats Discrepancy > AD Stats Discrepancy")
    print(f"  → AD Stats gives LOWER discrepancy values")
    print(f"  Mean improvement: {df['Difference'].mean():.6f}")
    print(f"  Median improvement: {df['Difference'].median():.6f}")
else:
    print(f"\nDirection: AD Stats Discrepancy > Stats Discrepancy")
    print(f"  → AD Stats gives HIGHER discrepancy values")

print(f"\nEffect size: r = {r_effect:.4f} ({'negligible' if r_effect<0.1 else 'small' if r_effect<0.3 else 'medium' if r_effect<0.5 else 'large'})")

# Final recommendation
print("\n" + "-" * 60)
print("RECOMMENDATION")
print("-" * 60)

if p_value < 0.001 and df['Difference'].mean() > 0 and r_effect >= 0.3:
    print("\n✓ AD Stats strategy shows statistically significant improvement")
    print("  with a moderate-to-large effect size.")
    print("\n  SUGGESTION: Proceed with AD Stats strategy.")
elif p_value < 0.001 and df['Difference'].mean() > 0 and r_effect >= 0.1:
    print("\n⚠️ AD Stats strategy shows statistically significant improvement")
    print("  but the effect size is small.")
    print("\n  SUGGESTION: Consider if the small improvement justifies")
    print("  any additional implementation costs.")
elif p_value < 0.001 and df['Difference'].mean() > 0:
    print("\n⚠️ AD Stats strategy shows statistically significant improvement")
    print("  but the effect size is negligible.")
    print("\n  SUGGESTION: The improvement is likely not practically meaningful.")
    print("  Stick with the regular Stats strategy.")
elif p_value < 0.05 and df['Difference'].mean() > 0:
    print("\n⚠️ AD Stats strategy shows statistically significant improvement")
    print("  at α=0.05 but NOT at α=0.001.")
    print("\n  SUGGESTION: Consider collecting more data or use with caution.")
else:
    print("\n✗ No significant improvement found.")
    print("\n  SUGGESTION: Keep using the regular Stats strategy.")

print("\n" + "=" * 60)
