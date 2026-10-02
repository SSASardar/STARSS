"""
3D_response_surface.py
3D surface plot showing Stats and AD Stats discrepancies
as functions of x'1 (apparent motion) and x'3 (sub-cloud gradient).
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import TwoSlopeNorm
from mpl_toolkits.mplot3d import Axes3D
from scipy.interpolate import griddata
import stylesheet  # Your centralized stylesheet

# ============================================================
# 1. LOAD DATA
# ============================================================

# Read the data
df = pd.read_csv('batch_test_20260914_110306/results_sums.txt', comment='#', sep=r'\s+',
                 header=None,
                 names=['x1', 'x2', 'x3', 'x4', 'x5', 'x6', 'x7',
                        'Stats_Discrepancy', 'AD_Stats_Discrepancy'])

print(f"Loaded {len(df):,} data points")

# ============================================================
# 2. PREPARE DATA FOR 3D SURFACE
# ============================================================

# x'1 = apparent motion = old x3 column
#   Stored value needs to be multiplied by 10 to recover true units (m/s).
x = df['x3']

# x'3 = sub-cloud gradient = old x5 column
#   Stored value needs to be divided by 10 and then 50 subtracted.
#   The result is in units of 1e-4 dBZ/m.
y = df['x5']/100 - 50

# --- Option B: uncomment the line below to convert to full dBZ/m ---
# y = (df['x5'] / 10 - 50) * 1e-4

z_stats = df['Stats_Discrepancy']
z_ad = df['AD_Stats_Discrepancy']

print(f"\nData ranges:")
print(f"  x'1 (apparent motion): {x.min():.2f} to {x.max():.2f} m/s")
print(f"  x'3 (sub-cloud gradient): {y.min():.2f} to {y.max():.2f} (x1e-4 dBZ/m)")
print(f"  Stats Discrepancy: {z_stats.min():.6f} to {z_stats.max():.6f}")
print(f"  AD Stats Discrepancy: {z_ad.min():.6f} to {z_ad.max():.6f}")

# ============================================================
# 3. CREATE REGULAR GRID FOR SMOOTH SURFACE
# ============================================================

# Define grid resolution
grid_resolution = 50

# Create grid points
xi = np.linspace(x.min(), x.max(), grid_resolution)
yi = np.linspace(y.min(), y.max(), grid_resolution)
xi, yi = np.meshgrid(xi, yi)

# Interpolate Stats data onto grid
z_stats_grid = griddata((x, y), z_stats, (xi, yi), method='cubic')
z_ad_grid = griddata((x, y), z_ad, (xi, yi), method='cubic')


# ============================================================
# 4. CREATE 3D PLOT WITH SOLID COLORS (NO COLORBARS)
# ============================================================

fig = plt.figure(figsize=(12, 8))
ax = fig.add_subplot(111, projection='3d')

# Stats surface (non-adaptive) - SOLID BLUE
surf_stats = ax.plot_surface(xi, yi, z_stats_grid, 
                             color=stylesheet.COLORS['blue'],
                             alpha=0.3,
                             linewidth=0,
                             antialiased=True,
                             shade=False)   # no shading grid

# AD Stats surface (adaptive) - SOLID PURPLE, same alpha as non-adaptive
surf_ad = ax.plot_surface(xi, yi, z_ad_grid, 
                          color=stylesheet.COLORS['purple'],
                          alpha=0.3,          # same as non-adaptive
                          linewidth=0,
                          antialiased=True,
                          shade=False)        # no shading grid

# ============================================================
# 4a. ADD FLAT PLANE AT Z=0 (FULL EXTENT)
# ============================================================

x_full = np.array([x.min(), x.max()])
y_full = np.array([y.min(), y.max()])

X_plane, Y_plane = np.meshgrid(x_full, y_full)
Z_plane = np.zeros_like(X_plane)

surf_zero = ax.plot_surface(X_plane, Y_plane, Z_plane,
                           color='gray',
                           alpha=0.15,
                           linewidth=0,
                           antialiased=True)

ax.plot_wireframe(X_plane, Y_plane, Z_plane,
                  color='gray', alpha=0.3, linewidth=0.5)

# ============================================================
# 5. CUSTOMIZE PLOT
# ============================================================

# Labels
ax.set_xlabel("Apparent Motion [m/s]", fontsize=11, labelpad=10)
ax.set_ylabel("Sub-cloud Gradient [$\\times 10^{-4}$ dBZ/m]", fontsize=11, labelpad=10)
ax.set_zlabel('Discrepancy in rainfall accumulation [mm/5min]', fontsize=11, labelpad=10)

# Set z-axis limits to include the zero plane
z_min = min(z_stats_grid.min(), z_ad_grid.min(), 0)
z_max = max(z_stats_grid.max(), z_ad_grid.max(), 0)
ax.set_zlim(z_min, z_max)

# Add legend with solid color patches
from matplotlib.patches import Patch
legend_elements = [Patch(facecolor=stylesheet.COLORS['blue'], alpha=0.3, label='Non-adaptive'),
                   Patch(facecolor=stylesheet.COLORS['purple'], alpha=0.3, label='Adaptive'),
                   Patch(facecolor='gray', alpha=0.4, label='Zero reference')]
ax.legend(handles=legend_elements, loc='best', fontsize=10)

# Adjust viewing angle for better visualization
ax.view_init(elev=25, azim=45)

# Add grid
ax.grid(True, alpha=0.3)


# ============================================================
# 6. SAVE FIGURE
# ============================================================

plt.savefig('figures/cs_3d_response_surface.png', dpi=300, bbox_inches='tight', pad_inches=0.5)
plt.savefig('figures/cs_3d_response_surface.pdf', bbox_inches='tight', pad_inches=0.5)
print("\nFigure saved: figures/cs_3d_response_surface.png and .pdf")

plt.show()

# ============================================================
# 7. 2D HEATMAP: DIFFERENCE SURFACE
# ============================================================

fig2, ax2 = plt.subplots(figsize=(10, 8))
fig2.patch.set_facecolor('white')

# Difference (Stats - AD)
z_diff_grid = z_stats_grid - z_ad_grid

# --- Handle NaNs from cubic interpolation at the convex hull edges ---
# Replace NaN with nearest-neighbor values so the colormap has no holes
z_diff_filled = griddata(
    (xi[~np.isnan(z_diff_grid)], yi[~np.isnan(z_diff_grid)]),
    z_diff_grid[~np.isnan(z_diff_grid)],
    (xi, yi),
    method='nearest'
)
# If there were no NaNs, keep the original
if np.isnan(z_diff_grid).any():
    z_diff_grid = z_diff_filled

# Create green-white-red colormap
from matplotlib.colors import LinearSegmentedColormap
colors_list = ['#d62728', '#ffffff', '#2ca02c']
cmap_diff = LinearSegmentedColormap.from_list('green_white_red', colors_list, N=256)

# --- Symmetric norm centered at 0 (fixes saturation skew) ---
abs_max = np.nanmax(np.abs(z_diff_grid))
norm = TwoSlopeNorm(vmin=-abs_max, vcenter=0, vmax=abs_max)

# Plot heatmap — use 'nearest' or 'none' interpolation to avoid
# resampling artifacts at save time
#im = ax2.imshow(z_diff_grid,
#                extent=[xi.min(), xi.max(), yi.min(), yi.max()],
#                origin='lower',
#                aspect='auto',
#                cmap=cmap_diff,
#                norm=norm,
#                interpolation='none')   # <-- was 'bilinear'

im = ax2.pcolormesh(xi, yi, z_diff_grid, cmap=cmap_diff, norm=norm, shading='auto')

# Add colorbar
cbar = fig2.colorbar(im, ax=ax2, shrink=0.8, aspect=20)
cbar.set_label('Difference in rainfall accumulation discrepancy [mm/5min]', fontsize=11)

# Labels
ax2.set_xlabel("Apparent Motion [m/s]", fontsize=12)
ax2.set_ylabel("Sub-cloud Gradient [$\\times 10^{-4}$ dBZ/m]", fontsize=12)

# Grid BELOW the image, not on top
ax2.set_axisbelow(True)
ax2.grid(True, alpha=0.3, linestyle='--', linewidth=0.5)

# Optional: text annotation
min_diff = np.nanmin(z_diff_grid)
max_diff = np.nanmax(z_diff_grid)
ax2.text(0.02, 0.98, f'Min: {min_diff:.3f}\nMax: {max_diff:.3f}',
         transform=ax2.transAxes, fontsize=9, verticalalignment='top',
         bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))

# Save — DO NOT use bbox_inches='tight' here; it triggers a re-draw
# that mangles the TwoSlopeNorm in some matplotlib versions.
plt.tight_layout()
plt.savefig('figures/cs_2d_difference_heatmap.png', dpi=300,
            facecolor='white', transparent=False)
plt.savefig('figures/cs_2d_difference_heatmap.pdf',
            facecolor='white', transparent=False)
print("Figure saved: figures/cs_2d_difference_heatmap.png and .pdf")

plt.show()

print("\nAll figures generated successfully!")
