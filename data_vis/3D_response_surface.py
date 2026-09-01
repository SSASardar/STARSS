"""
3D_response_surface.py
3D surface plot showing Stats and AD Stats discrepancies
as functions of apparent motion (x4) and cloud base height (x5).
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
df = pd.read_csv('batch_test_20260831_111605/results_sums.txt', comment='#', sep=r'\s+',
                 header=None,
                 names=['x1', 'x2', 'x3', 'x4', 'x5', 'x6', 'x7',
                        'Stats_Discrepancy', 'AD_Stats_Discrepancy'])

print(f"Loaded {len(df):,} data points")

# ============================================================
# 2. PREPARE DATA FOR 3D SURFACE
# ============================================================

# Extract variables
x = df['x4'] / 100  # Apparent motion (m/s) - convert back to original units
y = df['x5'] / 100  # Cloud base height (km) - convert back to original units
z_stats = df['Stats_Discrepancy']
z_ad = df['AD_Stats_Discrepancy']

print(f"\nData ranges:")
print(f"  Apparent motion: {x.min():.2f} to {x.max():.2f} m/s")
print(f"  Cloud base height: {y.min():.2f} to {y.max():.2f} km")
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

# Stats surface - SOLID BLUE (no gradient)
surf_stats = ax.plot_surface(xi, yi/10, z_stats_grid, 
                             color=stylesheet.COLORS['blue'],  # Solid blue
                             alpha=0.3,
                             linewidth=0,
                             antialiased=True)

# AD Stats surface - SOLID PURPLE (no gradient)
surf_ad = ax.plot_surface(xi, yi/10, z_ad_grid, 
                          color=stylesheet.COLORS['purple'],  # Solid purple
                          alpha=1,
                          linewidth=0,
                          antialiased=True)

# ============================================================
# 5. CUSTOMIZE PLOT
# ============================================================

# Labels
ax.set_xlabel('Apparent Motion [m/s]', fontsize=11, labelpad=10)
ax.set_ylabel('Cloud Base Height [km]', fontsize=11, labelpad=10)
ax.set_zlabel('Discrepancy in rainfall accumulation [mm/h]', fontsize=11, labelpad=10)

# Add legend with solid color patches
from matplotlib.patches import Patch
legend_elements = [Patch(facecolor=stylesheet.COLORS['blue'], alpha=0.8, label='Non-adaptive'),
                   Patch(facecolor=stylesheet.COLORS['purple'], alpha=0.8, label='Adaptive')]
ax.legend(handles=legend_elements, loc='best', fontsize=10)

# Adjust viewing angle for better visualization
ax.view_init(elev=25, azim=45)

# Add grid
ax.grid(True, alpha=0.3)


# ============================================================
# 6. SAVE FIGURE
# ============================================================

#plt.tight_layout()
# Use subplots_adjust instead of tight_layout for 3D plots
#plt.subplots_adjust(left=0.1, right=0.9, top=0.9, bottom=0.1)

plt.savefig('figures/cs_3d_response_surface.png', dpi=300, bbox_inches='tight', pad_inches=0.5)
plt.savefig('figures/cs_3d_response_surface.pdf', bbox_inches='tight', pad_inches=0.5)
print("\nFigure saved: figures/cs_3d_response_surface.png and .pdf")

plt.show()


# ============================================================
# 7. 2D HEATMAP: DIFFERENCE SURFACE
# ============================================================

# Create 2D heatmap
fig2, ax2 = plt.subplots(figsize=(10, 8))

# Difference (Stats - AD)
z_diff_grid = z_stats_grid - z_ad_grid

# Create green-white-red colormap
from matplotlib.colors import LinearSegmentedColormap
colors_list = ['#2ca02c', '#ffffff', '#d62728']  # Green -> White -> Red
cmap_diff = LinearSegmentedColormap.from_list('green_white_red', colors_list, N=256)

# Create norm centered at 0
norm = TwoSlopeNorm(vmin=z_diff_grid.min(), vcenter=0, vmax=z_diff_grid.max())

# Plot heatmap
im = ax2.imshow(z_diff_grid, 
                extent=[xi.min(), xi.max(), yi.min()/10, yi.max()/10],  # [xmin, xmax, ymin, ymax]
                origin='lower',  # Put origin at bottom-left
                aspect='auto',   # Adjust aspect ratio to fill plot
                cmap=cmap_diff,
                norm=norm,
                interpolation='bilinear')  # Smooth interpolation

# Add colorbar
cbar = fig2.colorbar(im, ax=ax2, shrink=0.8, aspect=20)
cbar.set_label('Difference in rainfall accumulation discrepancy [mm/h]', fontsize=11)

# Labels
ax2.set_xlabel('Apparent Motion [m/s]', fontsize=12)
ax2.set_ylabel('Cloud Base Height [km]', fontsize=12)

# Add contour lines to show the zero crossing
#contour = ax2.contour(xi, yi/10, z_diff_grid, levels=[0],
#                      colors='black', linewidths=1.5, linestyles='dashed')

# Add grid for better readability
ax2.grid(True, alpha=0.3, linestyle='--', linewidth=0.5)

# Optional: Add text annotation showing min/max difference
min_diff = z_diff_grid.min()
max_diff = z_diff_grid.max()
ax2.text(0.02, 0.98, f'Min: {min_diff:.3f}\nMax: {max_diff:.3f}', 
         transform=ax2.transAxes, fontsize=9, verticalalignment='top',
         bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))

# Save
plt.tight_layout()
plt.savefig('figures/cs_2d_difference_heatmap.png', dpi=300, bbox_inches='tight')
plt.savefig('figures/cs_2d_difference_heatmap.pdf', bbox_inches='tight')
print("Figure saved: figures/cs_2d_difference_heatmap.png and .pdf")

plt.show()

print("\nAll figures generated successfully!")
