"""
3D_response_surface.py
3D surface plot showing X, C, Combi, and AD stats discrepancies
as functions of x'1 (apparent motion) and x'3 (sub-cloud gradient).

Parameter space: 100 x 100 grid.

Also produces 3 absolute-difference heatmaps:
  |C| - |X|,  |C| - |Combi|,  |C| - |AD|
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import TwoSlopeNorm, LinearSegmentedColormap
from mpl_toolkits.mplot3d import Axes3D
from scipy.interpolate import griddata
from matplotlib.patches import Patch
import stylesheet

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

print(f"\nData ranges:")
print(f"  x'1 (apparent motion):     {x.min():.2f} to {x.max():.2f} m/s")
print(f"  x'3 (sub-cloud gradient):  {y.min():.2f} to {y.max():.2f} (x1e-4 dBZ/m)")
print(f"  X     Discrepancy: {z_x.min():.6f} to {z_x.max():.6f}")
print(f"  C     Discrepancy: {z_c.min():.6f} to {z_c.max():.6f}")
print(f"  Combi Discrepancy: {z_combi.min():.6f} to {z_combi.max():.6f}")
print(f"  AD    Discrepancy: {z_ad.min():.6f} to {z_ad.max():.6f}")

# ============================================================
# 3. REGULAR 100 x 100 GRID
# ============================================================

grid_resolution = 100   # <-- 100 x 100 parameter grid

xi = np.linspace(x.min(), x.max(), grid_resolution)
yi = np.linspace(y.min(), y.max(), grid_resolution)
xi, yi = np.meshgrid(xi, yi)

# 'linear' is well-behaved on a dense grid. Switch to 'cubic' if you
# prefer smoother surfaces and your data is well-distributed.
INTERP = 'linear'

z_x_grid     = griddata((x, y), z_x,     (xi, yi), method=INTERP)
z_c_grid     = griddata((x, y), z_c,     (xi, yi), method=INTERP)
z_combi_grid = griddata((x, y), z_combi, (xi, yi), method=INTERP)
z_ad_grid    = griddata((x, y), z_ad,    (xi, yi), method=INTERP)

# ============================================================
# 4. 3D PLOT — four surfaces
# ============================================================

# On a 100x100 grid each surface has ~10,000 quads. Draw every
# other row/column to keep the figure light and legible.
STRIDE = 4

fig = plt.figure(figsize=(13, 9))
ax = fig.add_subplot(111, projection='3d')

def draw(z_grid, color):
    return ax.plot_surface(
        xi, yi, z_grid,
        color=color,
        alpha=0.25,
        linewidth=0,
        antialiased=True,
        shade=False,
        rstride=STRIDE, cstride=STRIDE,
    )

surf_x     = draw(z_x_grid,     stylesheet.COLORS.get('blue',   'tab:blue'))
surf_c     = draw(z_c_grid,     stylesheet.COLORS.get('red',    'tab:red'))
surf_combi = draw(z_combi_grid, stylesheet.COLORS.get('green',  'tab:green'))
surf_ad    = draw(z_ad_grid,    stylesheet.COLORS.get('purple', 'tab:purple'))

# Zero plane
x_full = np.array([x.min(), x.max()])
y_full = np.array([y.min(), y.max()])
X_plane, Y_plane = np.meshgrid(x_full, y_full)
Z_plane = np.zeros_like(X_plane)

ax.plot_surface(X_plane, Y_plane, Z_plane,
                color='gray', alpha=0.2, linewidth=0, antialiased=True)
ax.plot_wireframe(X_plane, Y_plane, Z_plane,
                  color='gray', alpha=0.6, linewidth=0.5)

# Labels
ax.set_xlabel("Apparent Motion [m/s]", fontsize=11, labelpad=10)
ax.set_ylabel("Sub-cloud Reflectivity Gradient [$\\times 10^{-4}$ dBZ/m]",
              fontsize=11, labelpad=10)
ax.set_zlabel('Discrepancy in rainfall accumulation [mm]',
              fontsize=11, labelpad=10)

z_min = min(np.nanmin(z_x_grid), np.nanmin(z_c_grid),
            np.nanmin(z_combi_grid), np.nanmin(z_ad_grid), 0)
z_max = max(np.nanmax(z_x_grid), np.nanmax(z_c_grid),
            np.nanmax(z_combi_grid), np.nanmax(z_ad_grid), 0)
ax.set_zlim(z_min, z_max)

legend_elements = [
    Patch(facecolor=stylesheet.COLORS.get('blue',   'tab:blue'),   alpha=0.3, label='X-band'),
    Patch(facecolor=stylesheet.COLORS.get('red',    'tab:red'),    alpha=0.3, label='C-band'),
    Patch(facecolor=stylesheet.COLORS.get('green',  'tab:green'),  alpha=0.3, label='Combined processing'),
    Patch(facecolor=stylesheet.COLORS.get('purple', 'tab:purple'), alpha=0.3, label='Adaptive scanning'),
    Patch(facecolor='gray', alpha=0.4, label='Zero reference'),
]
ax.legend(handles=legend_elements, loc='best', fontsize=10)

ax.view_init(elev=25, azim=60)
ax.grid(True, alpha=0.3)

plt.savefig('figures/cs_3d_response_surface.png', dpi=300,
            bbox_inches='tight', pad_inches=0.5)
plt.savefig('figures/cs_3d_response_surface.pdf',
            bbox_inches='tight', pad_inches=0.5)
print("\nFigure saved: figures/cs_3d_response_surface.png and .pdf")
plt.show()


# ============================================================
# 5. ABSOLUTE-DIFFERENCE HEATMAP HELPER
# ============================================================

def plot_abs_difference_heatmap(z_ref_grid, z_other_grid,
                                ref_label, other_label, outname):
    """
    |ref| - |other|  heatmap.
    Green : |ref| > |other|  (other source has smaller error)
    Red   : |ref| < |other|  (other source has larger error)
    White : equal
    """
    fig_h, ax_h = plt.subplots(figsize=(10, 8))
    fig_h.patch.set_facecolor('white')

    z_diff = np.abs(z_ref_grid) - np.abs(z_other_grid)
    #z_diff = np.abs(z_ref_grid - z_other_grid)

    # Fill NaN edges (cubic/linear hull gaps) with nearest-neighbour
    if np.isnan(z_diff).any():
        z_diff = griddata(
            (xi[~np.isnan(z_diff)], yi[~np.isnan(z_diff)]),
            z_diff[~np.isnan(z_diff)],
            (xi, yi), method='nearest'
        )

    colors_list = ['#d62728', '#ffffff', '#2ca02c']
    cmap_diff = LinearSegmentedColormap.from_list('green_white_red',
                                                  colors_list, N=256)

    abs_max = np.nanmax(np.abs(z_diff))
    norm = TwoSlopeNorm(vmin=-abs_max, vcenter=0, vmax=abs_max)

    # 100x100 with shading='auto' renders without resampling artifacts
    im = ax_h.pcolormesh(xi, yi, z_diff,
                         cmap=cmap_diff, norm=norm, shading='auto')

    cbar = fig_h.colorbar(im, ax=ax_h, shrink=0.8, aspect=20)
    cbar.set_label(f'|{ref_label}| - |{other_label}|  [mm]', fontsize=11)

    ax_h.set_xlabel("Apparent Motion [m/s]", fontsize=12)
    ax_h.set_ylabel("Sub-cloud Reflectivity Gradient [$\\times 10^{-4}$ dBZ/m]", fontsize=12)

    ax_h.set_axisbelow(True)
    ax_h.grid(True, alpha=0.3, linestyle='--', linewidth=0.5)

    min_diff = np.nanmin(z_diff)
    max_diff = np.nanmax(z_diff)
    ax_h.text(0.02, 0.98,
              f'Min: {min_diff:.3f}\nMax: {max_diff:.3f}',
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
# 6. THREE ABSOLUTE-DIFFERENCE HEATMAPS (reference = C-band)
# ============================================================

#plot_abs_difference_heatmap(z_c_grid, z_x_grid,
#                            'C-band', 'X-band',
#                            'cs_2d_absdiff_C_minus_X')

#plot_abs_difference_heatmap(z_c_grid, z_combi_grid,
#                            'C-band', 'Combi',
#                            'cs_2d_absdiff_C_minus_Combi')

#plot_abs_difference_heatmap(z_c_grid, z_ad_grid,
#                            'C-band', 'Adaptive',
#                            'cs_2d_absdiff_C_minus_AD')

print("\nAll figures generated successfully!")
