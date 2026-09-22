import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import LogNorm
from matplotlib.ticker import LogLocator, ScalarFormatter
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
disp_C = load_grid("outputs/disp_C_g_0039.txt")
disp_X = load_grid("outputs/disp_X_g_0039.txt")
true_g = load_grid("outputs/true_g_0039.txt")

# Determine common color scale limits
vmin = min(np.nanmin(disp_C), np.nanmin(disp_X), np.nanmin(true_g))
vmax = max(np.nanmax(disp_C), np.nanmax(disp_X), np.nanmax(true_g))

norm = LogNorm(vmin=vmin, vmax=vmax)

# ===========================
# 2. COMPUTE TARGET SHAPE DYNAMICALLY
# ===========================

target_shape = (
    max(disp_C.shape[0], disp_X.shape[0], true_g.shape[0]),  # Max rows
    max(disp_C.shape[1], disp_X.shape[1], true_g.shape[1])   # Max cols
)

print(f"Original shapes:")
print(f"  disp_C: {disp_C.shape}")
print(f"  disp_X: {disp_X.shape}")
print(f"  true_g: {true_g.shape}")
print(f"Target shape: {target_shape}")

# ===========================
# 3. PAD ALL GRIDS TO TARGET SHAPE
# ===========================

disp_C_padded = pad_grid_to_match(disp_C, target_shape)
disp_X_padded = pad_grid_to_match(disp_X, target_shape)
true_g_padded = pad_grid_to_match(true_g, target_shape)

print(f"\nPadded shapes:")
print(f"  disp_C: {disp_C_padded.shape}")
print(f"  disp_X: {disp_X_padded.shape}")
print(f"  true_g: {true_g_padded.shape}")


# ===========================
# 4. FUNCTION TO CREATE INDIVIDUAL FIGURE
# ===========================

def create_single_figure(data, filename, vmin, vmax):
    """Create a single figure with the given data and save it."""
    fig, ax = plt.subplots(figsize=(6, 5))
    
    norm = LogNorm(vmin=vmin, vmax=vmax)
    
    im = ax.imshow(data.T,
                   cmap=stylesheet.COLORMAPS['sequential'],
                   norm=norm,
                   origin='lower')
    
    ax.set_xlabel("x [km]")
    ax.set_ylabel("y [km]")
    
    # Remove spines for cleaner look
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_visible(False)
    ax.spines['bottom'].set_visible(False)
    
    # Create colorbar with custom ticks
    cbar = fig.colorbar(im, ax=ax, orientation='vertical', pad=0.05)
    cbar.set_label("Reflectivity [dBZ]", fontsize=10)
    
    # Set custom ticks on the colorbar
    cbar.locator = LogLocator(base=10.0, subs=(1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0), numticks=20)
    cbar.formatter = ScalarFormatter()
    cbar.update_ticks()
    
    plt.savefig(f"{filename}.pdf", bbox_inches='tight')
    plt.savefig(f"{filename}.png", dpi=300, bbox_inches='tight')
    plt.show()
    plt.close(fig)


# ===========================
# 5. CREATE THREE INDIVIDUAL FIGURES
# ===========================

create_single_figure(true_g_padded, "figures/md_grid_true", vmin, vmax)
create_single_figure(disp_X_padded, "figures/md_grid_x", vmin, vmax)
create_single_figure(disp_C_padded, "figures/md_grid_c", vmin, vmax)


# Print some stats about the grids
print(f"Grid shapes:")
print(f"  disp_C: {disp_C.shape}")
print(f"  disp_X: {disp_X.shape}")
print(f"  true_g: {true_g.shape}")
print(f"Color scale: {vmin:.2f} to {vmax:.2f} dBZ")
