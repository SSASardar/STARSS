import os
import glob
import re
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import Normalize

# Ensure output directory exists
#os.makedirs("figures", exist_ok=True)

# ===========================
# 1. HELPER FUNCTIONS
# ===========================

def load_grid_with_metadata(filename, threshold=5):
    """
    Loads a grid file, parses its bottom-left reference point and grid resolution 
    from the header, converts units from meters to kilometers, and replaces 
    zero values and 'NaN' strings with np.nan.
    """
    values = []
    ref_point = None
    resolution_km = None
    
    with open(filename, "r") as f:
        for line in f:
            # Parse reference point (convert from meters to km)
            if "Ref point:" in line:
                match = re.search(r"Ref point:\s*\(([^,]+),\s*([^)]+)\)", line)
                if match:
                    ref_point = (float(match.group(1)) / 1000.0, float(match.group(2)) / 1000.0)
                continue
                
            # Parse grid resolution (convert from meters to km)
            if "Grid res:" in line:
                match = re.search(r"Grid res:\s*([^\s]+)\s*meters", line)
                if match:
                    resolution_km = float(match.group(1)) / 1000.0
                continue
                
            if line.startswith("#") or not line.strip():
                continue
            
            row = [float(tok) if tok.lower() != "nan" else np.nan for tok in line.split()]
            values.append(row)

    if not values:
        return None, None, None
        
    data = np.array(values)
    # Treat explicit zeros and low reflectivities as missing data
    data[data <= threshold] = np.nan
    return data, ref_point, resolution_km

def dbz_to_qpe(dbz, a=200.0, b=1.6):
    """Converts reflectivity (dBZ) to rainfall rate R (mm/h) via Marshall-Palmer."""
    if dbz is None or np.all(np.isnan(dbz)):
        return np.full_like(dbz, np.nan) if dbz is not None else None
    Z_linear = 10.0 ** (dbz / 10.0)
    return (Z_linear / a) ** (1.0 / b)

# ===========================
# 2. SINGLE-PASS DATA LOADING
# ===========================

file_paths = sorted(glob.glob("outputs/true_g_*.txt"))
timesteps = [re.search(r"true_g_(\d+)\.txt", f).group(1) for f in file_paths if re.search(r"true_g_(\d+)\.txt", f)]

if not timesteps:
    raise FileNotFoundError("No grid files found inside 'outputs/'. Check your paths.")

print(f"Found {len(timesteps)} timesteps. Processing metadata...")

grid_registry = []
global_min_x, global_max_x = np.inf, -np.inf
global_min_y, global_max_y = np.inf, -np.inf
detected_res = None

for step in timesteps:
    file_c = f"outputs/disp_C_g_{step}.txt"
    file_x = f"outputs/disp_X_g_{step}.txt"
    file_true = f"outputs/true_g_{step}.txt"
    
    if not (os.path.exists(file_c) and os.path.exists(file_x) and os.path.exists(file_true)):
        continue

    data_true, ref_true, res_true = load_grid_with_metadata(file_true)
    data_c, ref_c, res_c = load_grid_with_metadata(file_c)
    data_x, ref_x, res_x = load_grid_with_metadata(file_x)
    
    ref = ref_true or ref_c or ref_x
    res = res_true or res_c or res_x
    
    if ref is None or data_true is None or res is None:
        continue
        
    if detected_res is None:
        detected_res = res  

    qpe_true = dbz_to_qpe(data_true)
    qpe_c = dbz_to_qpe(data_c)
    qpe_x = dbz_to_qpe(data_x)
    
    rows, cols = qpe_true.shape
    x_min, y_min = ref[0], ref[1]
    
    # Strictly define the right boundary (x_max) to align with the fixed 130 km line
    x_max = x_min + (rows * res)
    y_max = y_min + (cols * res)
    
    global_min_x = min(global_min_x, x_min)
    global_max_x = max(global_max_x, x_max)
    global_min_y = min(global_min_y, y_min)
    global_max_y = max(global_max_y, y_max)
    
    grid_registry.append({
        'x_min': x_min, 'x_max': x_max, 'y_min': y_min,
        'qpe_true': qpe_true, 'qpe_c': qpe_c, 'qpe_x': qpe_x
    })

if detected_res is None:
    raise ValueError("Could not extract grid resolution from the files.")

dx = dy = detected_res
print(f"Detected resolution: {dx*1000.0:.1f} meters ({dx:.3f} km)")

# ===========================
# 3. BUILD THE GLOBAL CANVAS (ROBUST EXACT ALIGNMENT)
# ===========================

total_rows = int(np.round((global_max_x - global_min_x) / dx))
total_cols = int(np.round((global_max_y - global_min_y) / dy))
print(f"Allocating master matrix size: {total_rows} x {total_cols} indices")

TIME_STEP_HOURS = 5.0 / 60.0

global_true_qpe = np.zeros((total_rows, total_cols))
global_c_qpe = np.zeros((total_rows, total_cols))
global_x_qpe = np.zeros((total_rows, total_cols))

data_mask_true = np.zeros((total_rows, total_cols), dtype=bool)
data_mask_c = np.zeros((total_rows, total_cols), dtype=bool)
data_mask_x = np.zeros((total_rows, total_cols), dtype=bool)

for item in grid_registry:
    t_qpe, c_qpe, x_qpe = item['qpe_true'], item['qpe_c'], item['qpe_x']
    
    # --- True QPE ---
    if t_qpe is not None:
        end_row = int(np.round((item['x_max'] - global_min_x) / dx))
        start_row = end_row - t_qpe.shape[0]
        start_col = int(np.round((item['y_min'] - global_min_y) / dy))
        end_col = start_col + t_qpe.shape[1]
        
        if 0 <= start_row < end_row <= total_rows and 0 <= start_col < end_col <= total_cols:
            rain_increment = t_qpe * TIME_STEP_HOURS
            valid_mask = ~np.isnan(rain_increment)
            
            # Verkrijg de huidige uitsnede
            sub_grid = global_true_qpe[start_row:end_row, start_col:end_col]
            # Tel alleen op waar de data geldig (niet NaN) is
            global_true_qpe[start_row:end_row, start_col:end_col] = np.where(valid_mask, sub_grid + rain_increment, sub_grid)
            data_mask_true[start_row:end_row, start_col:end_col] |= valid_mask
        
    # --- C-band QPE ---
    if c_qpe is not None:
        end_row = int(np.round((item['x_max'] - global_min_x) / dx))
        start_row = end_row - c_qpe.shape[0]
        start_col = int(np.round((item['y_min'] - global_min_y) / dy))
        end_col = start_col + c_qpe.shape[1]
        
        if 0 <= start_row < end_row <= total_rows and 0 <= start_col < end_col <= total_cols:
            rain_increment = c_qpe * TIME_STEP_HOURS
            valid_mask = ~np.isnan(rain_increment)
            
            sub_grid = global_c_qpe[start_row:end_row, start_col:end_col]
            global_c_qpe[start_row:end_row, start_col:end_col] = np.where(valid_mask, sub_grid + rain_increment, sub_grid)
            data_mask_c[start_row:end_row, start_col:end_col] |= valid_mask
        
    # --- X-band QPE ---
    if x_qpe is not None:
        end_row = int(np.round((item['x_max'] - global_min_x) / dx))
        start_row = end_row - x_qpe.shape[0]  # Typefout x_x_qpe hier definitief hersteld
        start_col = int(np.round((item['y_min'] - global_min_y) / dy))
        end_col = start_col + x_qpe.shape[1]
        
        if 0 <= start_row < end_row <= total_rows and 0 <= start_col < end_col <= total_cols:
            rain_increment = x_qpe * TIME_STEP_HOURS
            valid_mask = ~np.isnan(rain_increment)
            
            sub_grid = global_x_qpe[start_row:end_row, start_col:end_col]
            global_x_qpe[start_row:end_row, start_col:end_col] = np.where(valid_mask, sub_grid + rain_increment, sub_grid)
            data_mask_x[start_row:end_row, start_col:end_col] |= valid_mask


# ===========================
# 4. COLOR SCALE & NORMALIZATION
# ===========================

all_accumulations = np.concatenate([
    global_true_qpe[data_mask_true],
    global_c_qpe[data_mask_c],
    global_x_qpe[data_mask_x]
])

if len(all_accumulations) > 0 and not np.all(np.isnan(all_accumulations)):
    vmin = 0.0  
    vmax = max(5.0, np.nanmax(all_accumulations))
else:
    vmin, vmax = 0.0, 10.0

norm = Normalize(vmin=vmin, vmax=vmax)

# ===========================
# 5. RENDER PLOT PANELS
# ===========================

print("Rendering plot panels...")
fig, axes = plt.subplots(1, 3, figsize=(15, 6), sharey=True)

try:
    import stylesheet
    cmap = stylesheet.COLORMAPS['sequential']
except ImportError:
    cmap = 'viridis'

extent = [global_min_x, global_max_x, global_min_y, global_max_y]

axes[0].imshow(global_true_qpe.T, cmap=cmap, norm=norm, origin='lower', extent=extent)
axes[0].set_title("True Rainfall Accumulation\n(Marshall-Palmer Sum)", fontsize=11)
axes[0].set_xlabel("x [km]")
axes[0].set_ylabel("y [km]")

axes[1].imshow(global_c_qpe.T, cmap=cmap, norm=norm, origin='lower', extent=extent)
axes[1].set_title("Measured Accumulation\n(C-band Composite)", fontsize=11)
axes[1].set_xlabel("x [km]")

im2 = axes[2].imshow(global_x_qpe.T, cmap=cmap, norm=norm, origin='lower', extent=extent)
axes[2].set_title("Measured Accumulation\n(X-band Composite)", fontsize=11)
axes[2].set_xlabel("x [km]")

for ax in axes:
    for s in ['top', 'right', 'left', 'bottom']:
        ax.spines[s].set_visible(False)

cbar = fig.colorbar(im2, ax=axes, orientation='horizontal', pad=0.18, aspect=45, shrink=0.75)
cbar.set_label("Total Rainfall Accumulation [mm]", fontsize=10)

plt.savefig("figures/QPE_comparison.png", dpi=300, bbox_inches='tight')
plt.savefig("figures/QPE_comparison.pdf", bbox_inches='tight')
plt.close(fig)

print("Success! Right-aligned stitched map saved at 'figures/QPE_comparison.png'")

