import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import LogNorm
import stylesheet  # centralised stylesheet

# ===========================
# 1. HELPER FUNCTIONS
# ===========================

def load_grid(filename, threshold = 5):
    """Load a grid file, skipping comment lines and handling NaN values."""
    values = []
    with open(filename, "r") as f:
        for line in f:
            if line.startswith("#") or not line.strip():
                continue
            row = [float(tok) if tok.lower() != "nan" else np.nan for tok in line.split()]
            values.append(row)

    data = np.array(values)

    # filter out low reflectivities to NAN.
    data[data<threshold] = np.nan

    return data

def pad_grid_to_match(grid, target_shape):
    """Pad grid with NaNs to match target shape."""
    padded = np.full(target_shape, np.nan)
    rows, cols = grid.shape
    target_rows, target_cols = target_shape
    rows_to_copy = min(rows, target_rows)
    cols_to_copy = min(cols, target_cols)
    padded[:rows_to_copy, :cols_to_copy] = grid[:rows_to_copy, :cols_to_copy]
    return padded

# ===========================
# 2. LOAD DATA
# ===========================

# Load the three grid files
disp_X = load_grid("outputs/cg_att_corr_measurement_0039.txt")
disp_IP = load_grid("outputs/cg_measured_0039.txt")
true_g = load_grid("outputs/cg_true_reflect_0039.txt")

# Determine common color scale limits
vmin = min(np.nanmin(disp_X), np.nanmin(disp_IP), np.nanmin(true_g))
vmax = max(np.nanmax(disp_X),np.nanmax(disp_IP), np.nanmax(true_g))

norm = LogNorm(vmin=vmin,vmax=vmax)
# ===========================
# 2. COMPUTE TARGET SHAPE DYNAMICALLY
# ===========================

target_shape = (
    max(disp_X.shape[0], disp_IP.shape[0], true_g.shape[0]),  # Max rows
    max(disp_X.shape[1], disp_IP.shape[1], true_g.shape[1])   # Max cols
)

print(f"Original shapes:")
print(f"  disp_X: {disp_X.shape}")
print(f"  disp_Intermediate_Product: {true_g.shape}")
print(f"  true_g: {true_g.shape}")
print(f"Target shape: {target_shape}")

# ===========================
# 3. PAD ALL GRIDS TO TARGET SHAPE
# ===========================

disp_X_padded = pad_grid_to_match(disp_X, target_shape)
disp_IP_padded = pad_grid_to_match(disp_IP, target_shape)
true_g_padded = pad_grid_to_match(true_g, target_shape)

print(f"\nPadded shapes:")
print(f"  disp_X: {disp_X_padded.shape}")
print(f"  disp_IP: {disp_IP_padded.shape}")
print(f"  true_g: {true_g_padded.shape}")



# ===========================
# 3. CREATE FIGURE WITH 3 SUBPLOTS
# ===========================

fig, axes = plt.subplots(1, 2, figsize=(15, 10), sharey=True)
#fig, axes = plt.subplots(1, 3, figsize=(21, 10), sharey=True)

# ===========================
# 4. PLOT EACH GRID
# ===========================

# Plot X-band measurement
im2 = axes[1].imshow(disp_X_padded.T[:,:-5], 
                     cmap=stylesheet.COLORMAPS['sequential'], 
                     norm = norm,
                     origin='lower')
axes[1].set_title("X-band intermediate product", fontsize=10)
axes[1].set_xlabel("surface [km]")
#axes[1].set_ylabel("height [km]")

# Plot X-band wihtout attenuation correction
#im2 = axes[1].imshow(disp_IP_padded.T[:,:-5], 
#                     cmap=stylesheet.COLORMAPS['sequential'], 
#                     norm = norm,
#                     origin='lower')
#axes[1].set_title("X-band without attenuation correction", fontsize=10)
#axes[1].set_xlabel("surface [km]")

# Plot True reflectivity
im3 = axes[0].imshow(true_g_padded.T[:,:-5], 
                     cmap=stylesheet.COLORMAPS['sequential'], 
                     norm = norm,
                     origin='lower')
axes[0].set_title("True Reflectivity", fontsize=10)
axes[0].set_xlabel("surface [km]")
axes[0].set_ylabel("height [km]")

# ===========================
# 5. ADD SINGLE COLORBAR
# ===========================

# Create colorbar that spans all three subplots
cbar = fig.colorbar(im2, ax=axes, orientation='horizontal', 
                    pad=0.15, aspect=40, shrink=0.8)
cbar.set_label("Reflectivity [dBZ]", fontsize=10)

# ===========================
# 6. APPLY STYLESHEET SETTINGS
# ===========================

# Remove spines for cleaner look (optional)
for ax in axes:
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_visible(False)
    ax.spines['bottom'].set_visible(False)

# ===========================
# 7. SAVE FIGURE
# ===========================

#plt.tight_layout()
plt.savefig("md_rhi_comparison.pdf", bbox_inches='tight')
plt.savefig("md_rhi_comparison.png", dpi=300, bbox_inches='tight')
plt.show()

# Print some stats about the grids
print(f"Grid shapes:")
print(f"  disp_X: {disp_X.shape}")
print(f"  true_g: {true_g.shape}")
print(f"Color scale: {vmin:.2f} to {vmax:.2f} dBZ")
