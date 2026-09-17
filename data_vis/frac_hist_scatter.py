"""
discrepancy_histograms_scatter.py

1. Overlaid histogram of discrepancy for:
     C-band PPI
     C-band PPI with X-band PPI  (combined)
     C-band PPI with X-band RHI  (adaptive)

2. Scatter of combined vs C-band, and adaptive vs C-band,
   with a 1:1 reference line.

Colours are drawn from stylesheet.COLORS.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import stylesheet

# ============================================================
# 1. LOAD DATA
# ============================================================

df = pd.read_csv('batch_test_response_surface/results_fracs.txt',
                 comment='#', sep=r'\s+', header=None,
                 names=['x1', 'x2', 'x3', 'x4', 'x5', 'x6', 'x7',
                        'X-band PPI',
                        'C-band PPI',
                        'C-band PPI with X-band PPI',
                        'C-band PPI with X-band RHI'])

print(f"Loaded {len(df):,} data points")

z_c     = df['C-band PPI'].values
z_combi = df['C-band PPI with X-band PPI'].values
z_ad    = df['C-band PPI with X-band RHI'].values

# Drop rows where any of the three is NaN so the histogram and the
# scatter use exactly the same set of parameter points.
mask = ~(np.isnan(z_c) | np.isnan(z_combi) | np.isnan(z_ad))
z_c, z_combi, z_ad = z_c[mask], z_combi[mask], z_ad[mask]
print(f"Usable points after NaN removal: {len(z_c):,}")

# ============================================================
# 2. COLOURS FROM STYLESHEET
# ============================================================

# C-band uses 'red' (a mid red), the combined uses 'teal',
# the adaptive uses 'purple'. All three come straight from
# stylesheet.COLORS, so changing the stylesheet recolours
# every figure automatically.
col_c     = stylesheet.COLORS['red']      # C-band
col_combi = stylesheet.COLORS['teal']     # combined
col_ad    = stylesheet.COLORS['purple']   # adaptive

# ============================================================
# 3. HISTOGRAM — overlaid, step-filled style (raw counts)
# ============================================================

fig, ax = plt.subplots(figsize=(7, 5))

# Common bin edges so the three distributions are directly comparable.
all_vals = np.concatenate([z_c, z_combi, z_ad])
bins = np.linspace(all_vals.min(), all_vals.max(), 60)

# Raw counts, not density.
hist_c,     edges = np.histogram(z_c,     bins=bins)
hist_combi, _     = np.histogram(z_combi, bins=bins)
hist_ad,    _     = np.histogram(z_ad,    bins=bins)

centres = 0.5 * (edges[:-1] + edges[1:])

ax.step(centres, hist_c,
        where='mid', color=col_c, linewidth=1.6,
        label='C-band PPI')
ax.fill_between(centres, hist_c, step='mid',
                color=col_c, alpha=0.25)

ax.step(centres, hist_combi,
        where='mid', color=col_combi, linewidth=1.6,
        label='C-band PPI + X-band PPI (combined)')
ax.fill_between(centres, hist_combi, step='mid',
                color=col_combi, alpha=0.25)

ax.step(centres, hist_ad,
        where='mid', color=col_ad, linewidth=1.6,
        label='C-band PPI + X-band RHI (adaptive)')
ax.fill_between(centres, hist_ad, step='mid',
                color=col_ad, alpha=0.25)

# Zero reference line
ax.axvline(0, color='black', linewidth=0.8,
           linestyle='--', alpha=0.6, zorder=0)

ax.set_xlabel('Percentage error')
ax.set_ylabel('Count')
ax.set_title('Distribution of percentage error', pad=10)

ax.set_axisbelow(True)
ax.grid(True, alpha=0.3, linestyle='--', linewidth=0.5)
ax.legend(loc='best', framealpha=0.9)

plt.tight_layout()
plt.savefig('figures/cs_perc_error_histogram.png',
            facecolor='white', transparent=False)
plt.savefig('figures/cs_perc_error_histogram.pdf',
            facecolor='white', transparent=False)
print("\nFigure saved: figures/cs_perc_error_histogram.png and .pdf")
plt.show()


# ============================================================
# 5. QUICK NUMERIC SUMMARY (printed to console)
# ============================================================

def summarise(name, arr):
    print(f"\n{name}")
    print(f"  N        : {len(arr)}")
    print(f"  Mean     : {np.mean(arr):+.4f} mm")
    print(f"  Median   : {np.median(arr):+.4f} mm")
    print(f"  Std dev  : {np.std(arr):.4f} mm")
    print(f"  Min/Max  : {arr.min():+.4f} / {arr.max():+.4f}")

print("\n=============================================")
print(" Discrepancy summary (signed)")
print("=============================================")
summarise('C-band PPI',                         z_c)
summarise('C-band PPI + X-band PPI (combined)', z_combi)
summarise('C-band PPI + X-band RHI (adaptive)', z_ad)

print("\n=============================================")
print(" Absolute-discrepancy summary")
print(" (smaller is better)")
print("=============================================")
summarise('|C-band PPI|',               np.abs(z_c))
summarise('|C-band + X-band PPI|',      np.abs(z_combi))
summarise('|C-band + X-band RHI|',      np.abs(z_ad))

print("\nAll figures generated successfully!")
