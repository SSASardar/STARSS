"""
2D_discrepancy_maps.py
Four 2D heatmaps of the signed discrepancy for each processing mode:
  X-band, C-band, Combi, Adaptive

One shared diverging colormap and one shared colour range, so the
colourbar is directly comparable across all four figures.

Parameter space: 100 x 100 grid.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import TwoSlopeNorm, LinearSegmentedColormap
from scipy.interpolate import griddata

# ============================================================
# 1. LOAD DATA
# ============================================================

df = pd.read_csv('batch_test_response_surface/results_sums.txt',
                 comment='#', sep=r'\s+', header=None,
                 names=['x1', 'x2', 'x3', 'x4', 'x5', 'x6', 'x7',
                        'X-band PPI',
                        'C-band PPI',
                        'C-band PPI with X-band PPI',
                        'C-band PPI with X-band RHI'])

print(f"Loaded {len(df):,} data points")

# ============================================================
# 2. PREPARE DATA
# ============================================================

x = df['x3'] / 100           # apparent motion [m/s]
y = df['x5'] / 100 - 50      # sub-cloud gradient [x1e-4 dBZ/m]

z_x     = df['X-band PPI']
z_c     = df['C-band PPI']
z_combi = df['C-band PPI with X-band PPI']
z_ad    = df['C-band PPI with X-band RHI']

# ============================================================
# 3. REGULAR 100 x 100 GRID
# ============================================================

grid_resolution = 100

xi = np.linspace(x.min(), x.max(), grid_resolution)
yi = np.linspace(y.min(), y.max(), grid_resolution)
xi, yi = np.meshgrid(xi, yi)

INTERP = 'linear'

def build_grid(z):
    """Interpolate onto the regular grid and fill NaN hull edges."""
    g = griddata((x, y), z, (xi, yi), method=INTERP)
    if np.isnan(g).any():
        g = griddata(
            (xi[~np.isnan(g)], yi[~np.isnan(g)]),
            g[~np.isnan(g)],
            (xi, yi), method='nearest'
        )
    return g

z_x_grid     = build_grid(z_x)
z_c_grid     = build_grid(z_c)
z_combi_grid = build_grid(z_combi)
z_ad_grid    = build_grid(z_ad)

# ============================================================
# 4. SHARED DIVERGING COLOURMAP AND SHARED RANGE
# ============================================================


cmap_shared = LinearSegmentedColormap.from_list(
    'BrBG',
    ['#543005', '#8c510a', '#bf812d', '#dfc27d', '#f6e8c3',
     '#f5f5f5',
     '#c7eae5', '#80cdc1', '#35978f', '#01665e', '#003c30'],
    N=256
)


# Single shared range across all four plots, symmetric about 0
all_vals = np.concatenate([
    z_x_grid[~np.isnan(z_x_grid)].ravel(),
    z_c_grid[~np.isnan(z_c_grid)].ravel(),
    z_combi_grid[~np.isnan(z_combi_grid)].ravel(),
    z_ad_grid[~np.isnan(z_ad_grid)].ravel(),
])
abs_max = np.nanmax(np.abs(all_vals))
shared_norm = TwoSlopeNorm(vmin=-abs_max, vcenter=0, vmax=abs_max)

print(f"\nShared colour range: {-abs_max:.4f} to {+abs_max:.4f} mm")

# ============================================================
# 5. HELPER: one signed-discrepancy heatmap
# ============================================================

def plot_signed_discrepancy(z_grid, title, outname):
    """
    Heatmap of a signed discrepancy field using the shared
    colormap and shared TwoSlopeNorm.
    """
    fig_h, ax_h = plt.subplots(figsize=(10, 8))
    fig_h.patch.set_facecolor('white')

    im = ax_h.pcolormesh(xi, yi, z_grid,
                         cmap=cmap_shared, norm=shared_norm,
                         shading='auto')

    cbar = fig_h.colorbar(im, ax=ax_h, shrink=0.8, aspect=20)
    cbar.set_label('Discrepancy in rainfall accumulation [mm]',
                   fontsize=11)
    # Force the colourbar ticks to span the shared range
    cbar.set_ticks(np.linspace(-abs_max, abs_max, 9))

    ax_h.set_xlabel("Apparent Motion [m/s]", fontsize=12)
    ax_h.set_ylabel("Sub-cloud Reflectivity Gradient "
                    "[$\\times 10^{-4}$ dBZ/m]", fontsize=12)
#    ax_h.set_title(title, fontsize=13, pad=10)

    ax_h.set_axisbelow(True)
    ax_h.grid(True, alpha=0.3, linestyle='--', linewidth=0.5)

    min_val = np.nanmin(z_grid)
    max_val = np.nanmax(z_grid)
    ax_h.text(0.02, 0.98,
              f'Min: {min_val:.3f}\nMax: {max_val:.3f}',
              transform=ax_h.transAxes, fontsize=9,
              verticalalignment='top',
              bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))

    plt.tight_layout()
    plt.savefig(f'figures/{outname}.png', dpi=300,
                facecolor='white', transparent=False)
    plt.savefig(f'figures/{outname}.pdf',
                facecolor='white', transparent=False)
    print(f"Figure saved: figures/{outname}.png and .pdf")
    plt.show()


# ============================================================
# 6. GENERATE THE FOUR MAPS
# ============================================================

plot_signed_discrepancy(z_x_grid,
                        'X-band PPI Discrepancy',
                        'cs_2d_discrepancy_X')

plot_signed_discrepancy(z_c_grid,
                        'C-band PPI Discrepancy',
                        'cs_2d_discrepancy_C')

plot_signed_discrepancy(z_combi_grid,
                        'C-band PPI with X-band PPI Discrepancy',
                        'cs_2d_discrepancy_Combi')

plot_signed_discrepancy(z_ad_grid,
                        'C-band PPI with X-band RHI Discrepancy',
                        'cs_2d_discrepancy_Adaptive')

print("\nAll four 2D discrepancy maps generated successfully!")
