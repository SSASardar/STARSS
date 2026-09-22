import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import LogNorm
from matplotlib.ticker import FixedLocator, ScalarFormatter
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
vmax = max(np.nanmax(disp_X), np.nanmax(disp_IP), np.nanmax(true_g))

norm = LogNorm(vmin=vmin, vmax=vmax)

# ===========================
# 2. COMPUTE TARGET SHAPE DYNAMICALLY
# ===========================

target_shape = (
    max(disp_X.shape[0], disp_IP.shape[0], true_g.shape[0]),  # Max rows
    max(disp_X.shape[1], disp_IP.shape[1], true_g.shape[1])   # Max cols
)

print(f"Original shapes:")
print(f"  disp_X: {disp_X.shape}")
print(f"  disp_Intermediate_Product: {disp_IP.shape}")
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
# 4. HELPER FUNCTION TO CREATE INDIVIDUAL FIGURE
# ===========================

def create_single_rhi_figure(data, filename, vmin, vmax):
    """Create a single RHI figure with its own x/y labels and horizontal colorbar underneath."""
    fig, ax = plt.subplots(figsize=(6, 6))

    norm = LogNorm(vmin=vmin, vmax=vmax)

    im = ax.imshow(data.T[:, :-5],
                   cmap=stylesheet.COLORMAPS['sequential'],
                   norm=norm,
                   origin='lower')

    ax.set_xlabel("surface [km]")
    ax.set_ylabel("height [km]")

    # Style cleanup: hide spines
    for s in ['top', 'right', 'left', 'bottom']:
        ax.spines[s].set_visible(False)

    # Add horizontal colorbar underneath the plot
    cbar = fig.colorbar(im, ax=ax, orientation='horizontal', pad=0.12, aspect=35, shrink=0.85)
    cbar.set_label("Reflectivity [dBZ]", fontsize=10)

    # Force dBZ ticks at 10, 20, 30, ... on the log colorbar
    tick_values = [10, 20, 30, 40, 50, 60, 70, 80, 90, 100]
    tick_values = [t for t in tick_values if vmin <= t <= vmax]
    if tick_values:
        cbar.locator = FixedLocator(tick_values)
        cbar.formatter = ScalarFormatter()
        cbar.update_ticks()

    # Save high-res outputs
    plt.savefig(f"{filename}.png", dpi=300, bbox_inches='tight')
    plt.savefig(f"{filename}.pdf", bbox_inches='tight')
    plt.show()
    plt.close(fig)

# ===========================
# 5. CREATE THE TWO INDIVIDUAL FIGURES
# ===========================

create_single_rhi_figure(true_g_padded, "figures/md_rhi_true", vmin, vmax)
create_single_rhi_figure(disp_X_padded, "figures/md_rhi_x", vmin, vmax)

# Print some stats about the grids
print(f"Grid shapes:")
print(f"  disp_X: {disp_X.shape}")
print(f"  true_g: {true_g.shape}")
print(f"Color scale: {vmin:.2f} to {vmax:.2f} dBZ")
