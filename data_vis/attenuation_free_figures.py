"""
Consolidated plotting programme.

Generates:
  1. QPE rainfall accumulation maps (three individual figures)
  2. VPR stratiform & convective comparisons (two individual figures)
  3. Rainfall accumulation graph (per-5-min, with lifecycle shading)

All output filenames use the prefix "md_far_".
"""

import os
import glob
import re
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import Normalize

import stylesheet  # centralised stylesheet

# Ensure output directories exist
os.makedirs("figures", exist_ok=True)

# ===========================================================================
# SHARED HELPERS
# ===========================================================================

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
            if "Ref point:" in line:
                match = re.search(r"Ref point:\s*\(([^,]+),\s*([^)]+)\)", line)
                if match:
                    ref_point = (float(match.group(1)) / 1000.0,
                                 float(match.group(2)) / 1000.0)
                continue

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
    data[data <= threshold] = np.nan
    return data, ref_point, resolution_km


def dbz_to_qpe(dbz, a=200.0, b=1.6):
    """Converts reflectivity (dBZ) to rainfall rate R (mm/h) via Marshall-Palmer."""
    if dbz is None or np.all(np.isnan(dbz)):
        return np.full_like(dbz, np.nan) if dbz is not None else None
    Z_linear = 10.0 ** (dbz / 10.0)
    return (Z_linear / a) ** (1.0 / b)


# ===========================================================================
# SECTION 1: QPE RAINFALL ACCUMULATION MAPS
# ===========================================================================

def generate_qpe_accumulation():
    print("\n" + "=" * 60)
    print("SECTION 1: QPE rainfall accumulation maps")
    print("=" * 60)

    file_paths = sorted(glob.glob("outputs/true_g_*.txt"))
    timesteps = [re.search(r"true_g_(\d+)\.txt", f).group(1)
                 for f in file_paths if re.search(r"true_g_(\d+)\.txt", f)]

    if not timesteps:
        raise FileNotFoundError("No grid files found inside 'outputs/'.")

    print(f"Found {len(timesteps)} timesteps.")

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
        x_max = x_min + (rows * res)
        y_max = y_min + (cols * res)

        global_min_x = min(global_min_x, x_min)
        global_max_x = max(global_max_x, x_max)
        global_min_y = min(global_min_y, y_min)
        global_max_y = max(global_max_y, y_max)

        grid_registry.append({
            'x_min': x_min, 'y_min': y_min,
            'qpe_true': qpe_true, 'qpe_c': qpe_c, 'qpe_x': qpe_x
        })

    if detected_res is None:
        raise ValueError("Could not extract grid resolution from the files.")

    dx = dy = detected_res
    total_rows = int(np.round((global_max_x - global_min_x) / dx))
    total_cols = int(np.round((global_max_y - global_min_y) / dy))

    TIME_STEP_HOURS = 5.0 / 60.0

    global_true_qpe = np.zeros((total_rows, total_cols))
    global_c_qpe = np.zeros((total_rows, total_cols))
    global_x_qpe = np.zeros((total_rows, total_cols))

    data_mask_true = np.zeros((total_rows, total_cols), dtype=bool)
    data_mask_c = np.zeros((total_rows, total_cols), dtype=bool)
    data_mask_x = np.zeros((total_rows, total_cols), dtype=bool)

    for item in grid_registry:
        start_row = int(np.floor((item['x_min'] - global_min_x) / dx))
        start_col = int(np.floor((item['y_min'] - global_min_y) / dy))

        for key, gmat, dmask in [
            ('qpe_true', global_true_qpe, data_mask_true),
            ('qpe_c', global_c_qpe, data_mask_c),
            ('qpe_x', global_x_qpe, data_mask_x),
        ]:
            arr = item[key]
            if arr is None:
                continue
            end_row = min(start_row + arr.shape[0], total_rows)
            end_col = min(start_col + arr.shape[1], total_cols)
            slice_row = end_row - start_row
            slice_col = end_col - start_col

            rain_increment = arr[:slice_row, :slice_col] * TIME_STEP_HOURS
            valid_mask = ~np.isnan(rain_increment)

            gmat[start_row:end_row, start_col:end_col][valid_mask] += rain_increment[valid_mask]
            dmask[start_row:end_row, start_col:end_col] |= valid_mask

    global_true_qpe[~data_mask_true] = np.nan
    global_c_qpe[~data_mask_c] = np.nan
    global_x_qpe[~data_mask_x] = np.nan

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

    try:
        cmap = stylesheet.COLORMAPS['sequential']
    except Exception:
        cmap = 'viridis'

    extent = [global_min_x, global_max_x, global_min_y, global_max_y]

    def _plot(data, filename):
        fig, ax = plt.subplots(figsize=(6, 6))
        norm = Normalize(vmin=vmin, vmax=vmax)
        im = ax.imshow(data.T, cmap=cmap, norm=norm,
                       origin='lower', extent=extent)
        ax.set_xlabel("x [km]")
        ax.set_ylabel("y [km]")
        for s in ['top', 'right', 'left', 'bottom']:
            ax.spines[s].set_visible(False)

        cbar = fig.colorbar(im, ax=ax, orientation='horizontal',
                            pad=0.12, aspect=35, shrink=0.85)
        cbar.set_label("Total Rainfall Accumulation [mm]", fontsize=10)

        plt.savefig(f"{filename}.png", dpi=300, bbox_inches='tight')
        plt.savefig(f"{filename}.pdf", bbox_inches='tight')
        plt.show()
        plt.close(fig)

    _plot(global_true_qpe, "figures/md_far_QPE_true")
    _plot(global_c_qpe, "figures/md_far_QPE_c")
    _plot(global_x_qpe, "figures/md_far_QPE_x")


# ===========================================================================
# SECTION 2: VPR COMPARISON
# ===========================================================================

def load_vpr_file_emp(filename, timestep=39):
    """
    Load a VPR file and extract a specific timestep (empirical format).
    Zeros in the reflectivity column are treated as missing data (NaN),
    since they correspond to bins with no measurements.
    """
    with open(filename, 'r') as f:
        lines = f.readlines()

    timesteps = []
    current = []
    for line in lines:
        line = line.strip()
        if not line:
            if current:
                timesteps.append(current)
                current = []
        elif line.startswith('#'):
            continue
        else:
            current.append(line)
    if current:
        timesteps.append(current)

    if timestep >= len(timesteps):
        print(f"Warning: Only {len(timesteps)} timesteps available. Using last.")
        timestep = -1

    heights, reflectivity = [], []
    for line in timesteps[timestep]:
        parts = line.split()
        if len(parts) >= 5:
            refl = float(parts[3])
            heights.append(float(parts[1]))
            # Treat zeros as missing measurements
            reflectivity.append(refl if refl != 0.0 else np.nan)
    return np.array(heights), np.array(reflectivity)


def load_vpr_file_true(filename, timestep=39):
    """Load a VPR file and extract a specific timestep (true format)."""
    with open(filename, 'r') as f:
        lines = f.readlines()

    timesteps = []
    current = []
    for line in lines:
        line = line.strip()
        if not line:
            if current:
                timesteps.append(current)
                current = []
        elif line.startswith('#'):
            continue
        else:
            current.append(line)
    if current:
        timesteps.append(current)

    if timestep >= len(timesteps):
        print(f"Warning: Only {len(timesteps)} timesteps available. Using last.")
        timestep = -1

    heights, reflectivity = [], []
    for line in timesteps[timestep]:
        parts = line.split()
        if len(parts) >= 3:
            heights.append(float(parts[1]))
            reflectivity.append(float(parts[2]))
    return np.array(heights), np.array(reflectivity)


def generate_vpr_plots():
    print("\n" + "=" * 60)
    print("SECTION 2: VPR comparisons")
    print("=" * 60)

    TIMESTEP = 39

    heights_strat_true, refl_strat_true = load_vpr_file_true("outputs/vpr_true_strat.txt", TIMESTEP)
    heights_strat_emp, refl_strat_emp = load_vpr_file_emp("outputs/vpr_emp_strat_rhi.txt", TIMESTEP)
    heights_strat_emp_C, refl_strat_emp_C = load_vpr_file_emp("outputs/vpr_emp_strat_C.txt", TIMESTEP)
    heights_strat_emp_X, refl_strat_emp_X = load_vpr_file_emp("outputs/vpr_emp_strat_X.txt", TIMESTEP)

    heights_conv_true, refl_conv_true = load_vpr_file_true("outputs/vpr_true_conv.txt", TIMESTEP)
    heights_conv_emp, refl_conv_emp = load_vpr_file_emp("outputs/vpr_emp_conv_rhi.txt", TIMESTEP)
    heights_conv_emp_C, refl_conv_emp_C = load_vpr_file_emp("outputs/vpr_emp_conv_C.txt", TIMESTEP)
    heights_conv_emp_X, refl_conv_emp_X = load_vpr_file_emp("outputs/vpr_emp_conv_X.txt", TIMESTEP)

    def _plot(heights_true, refl_true,
              heights_emp, refl_emp,
              heights_emp_C, refl_emp_C,
              heights_emp_X, refl_emp_X,
              filename, inset_xlim, inset_ylim):

        fig, ax = plt.subplots(figsize=(6, 6))

        ax.plot(refl_true[0:18], heights_true[0:18],
                color=stylesheet.COLORS['black'], linestyle='-',
                linewidth=1, markersize=3, label='True')

        ax.plot(refl_emp_C[0:18], heights_emp_C[0:18],
                color='red', linestyle='-.',
                linewidth=1, marker='^', markersize=3, label='PPI-based (C-band)')

        ax.plot(refl_emp_X[0:18], heights_emp_X[0:18],
                color=stylesheet.COLORS['black'], linestyle='-.',
                linewidth=1, marker='o', markersize=3, label='PPI-based (X-band)')

        ax.plot(refl_emp[0:18], heights_emp[0:18],
                color=stylesheet.COLORS['black'], linestyle=':',
                linewidth=1, marker='o', markersize=3, label='RHI-based (X-band)')

        ax.set_xlabel("Reflectivity [dBZ]", fontsize=10)
        ax.set_ylabel("Height [km]", fontsize=10)
        ax.legend(loc='best', fontsize=11)
        ax.grid(True, linestyle=':', alpha=0.5, linewidth=0.5)

        for s in ['top', 'right']:
            ax.spines[s].set_visible(False)

        # Inset in bottom-left corner
        ax_inset = ax.inset_axes([0.05, 0.05, 0.4, 0.4])

        ax_inset.plot(refl_true[0:9], heights_true[0:9],
                      color=stylesheet.COLORS['black'], linestyle='-',
                      linewidth=1, markersize=3)
        ax_inset.plot(refl_emp_C[0:9], heights_emp_C[0:9],
                      color='red', linestyle='-.',
                      linewidth=1, marker='^', markersize=3)
        ax_inset.plot(refl_emp_X[0:9], heights_emp_X[0:9],
                      color=stylesheet.COLORS['black'], linestyle='-.',
                      linewidth=1, marker='o', markersize=3)
        ax_inset.plot(refl_emp[0:9], heights_emp[0:9],
                      color=stylesheet.COLORS['black'], linestyle=':',
                      linewidth=1, marker='o', markersize=3)

        ax_inset.set_xlim(inset_xlim[0], inset_xlim[1])
        ax_inset.set_ylim(inset_ylim[0], inset_ylim[1])
        ax_inset.grid(True, linestyle=':', alpha=0.4, linewidth=0.4)
        ax_inset.tick_params(labelsize=7)

        plt.savefig(f"{filename}.png", dpi=300, bbox_inches='tight')
        plt.savefig(f"{filename}.pdf", bbox_inches='tight')
        plt.show()
        plt.close(fig)

    _plot(heights_strat_true, refl_strat_true,
          heights_strat_emp, refl_strat_emp,
          heights_strat_emp_C, refl_strat_emp_C,
          heights_strat_emp_X, refl_strat_emp_X,
          "figures/md_far_vpr_stratiform",
          inset_xlim=(26, 45), inset_ylim=(0, 5))

    _plot(heights_conv_true, refl_conv_true,
          heights_conv_emp, refl_conv_emp,
          heights_conv_emp_C, refl_conv_emp_C,
          heights_conv_emp_X, refl_conv_emp_X,
          "figures/md_far_vpr_convective",
          inset_xlim=(45, 50), inset_ylim=(0, 5))


# ===========================================================================
# SECTION 3: RAINFALL ACCUMULATION GRAPH (per-5-min, with lifecycle shading)
# ===========================================================================

def generate_rainfall_accumulation_graph():
    print("\n" + "=" * 60)
    print("SECTION 3: Rainfall accumulation graph")
    print("=" * 60)

    # Load C dataset
    stats_C = np.loadtxt("outputs/stats_C.txt", skiprows=1)
    scan_id_C = stats_C[:, 0]
    total_measured_mm2_C = stats_C[:, 6]
    total_true_mm2_C = stats_C[:, 7]
    time_C = scan_id_C * 5.0  # minutes

    # Load X dataset
    stats_X = np.loadtxt("outputs/stats_X.txt", skiprows=1)
    scan_id_X = stats_X[:, 0]
    total_measured_mm2_X = stats_X[:, 6]
    time_X = scan_id_X * 5.0  # minutes

    fig, ax = plt.subplots(figsize=(12, 4))

    # Dataset - True
    ax.plot(time_C, total_true_mm2_C,
            color=stylesheet.COLORS['black'],
            label='True',
            linewidth=1,
            markersize=3)

    # Dataset C - Measured
    ax.plot(time_C, total_measured_mm2_C,
            marker='^',
            color=stylesheet.COLORS['black'],
            label='C-band QPE',
            linewidth=1,
            markersize=3,
            linestyle='-.')

    # Dataset X - Measured
    ax.plot(time_X, total_measured_mm2_X,
            marker='o',
            color=stylesheet.COLORS['black'],
            label='X-band QPE',
            linewidth=1,
            markersize=3,
            linestyle='-.')

    ax.set_xlim(left=0)

    # Vertical lines at lifecycle boundaries
    # MATURE/DECAY boundary (t3) and DECAY end (t5) shifted one step (5 min) earlier.
    t1, t2, t3, t4, t5 = 60, 120, 165, 200, 225
    for t in (t1, t2, t3, t5):
        ax.axvline(t, color='black', linestyle='--', linewidth=0.8, alpha=0.7)

    # Shaded regions
    xmin, xmax = ax.get_xlim()
    ymin, ymax = ax.get_ylim()
    y_range = ymax - ymin

    # UNINITIATED
    ax.axvspan(0, t1, alpha=0.15, color=stylesheet.COLORS['strat'], label='_nolegend_')
    ax.text(0.05 * t1, ymax - 0.05 * y_range, 'UNINITIATED',
            ha='left', va='top', fontsize=9, fontweight='bold',
            color=stylesheet.COLORS['strat'], alpha=1)

    # GROWTH
    ax.axvspan(t1, t2, alpha=0.15, color=stylesheet.COLORS['growth'], label='_nolegend_')
    ax.text(t1 + 0.05 * (t2 - t1), ymax - 0.05 * y_range, 'GROWTH',
            ha='left', va='top', fontsize=9, fontweight='bold',
            color=stylesheet.COLORS['growth'], alpha=1)

    # MATURE
    ax.axvspan(t2, t3, alpha=0.15, color=stylesheet.COLORS['mature'], label='_nolegend_')
    ax.text(t2 + 0.05 * (t3 - t2), ymax - 0.05 * y_range, 'MATURE',
            ha='left', va='top', fontsize=9, fontweight='bold',
            color=stylesheet.COLORS['mature'], alpha=1)

    # DECAY
    ax.axvspan(t3, t5, alpha=0.15, color=stylesheet.COLORS['decay'], label='_nolegend_')
    ax.text(t3 + 0.05 * (t5 - t3), ymax - 0.05 * y_range, 'DECAY',
            ha='left', va='top', fontsize=9, fontweight='bold',
            color=stylesheet.COLORS['decay'], alpha=1)

    # POST-DECAY
    ax.axvspan(t5, xmax, alpha=0.15, color=stylesheet.COLORS['strat'], label='_nolegend_')
    ax.text(t5 + 0.05 * (xmax - t5), ymax - 0.05 * y_range, '',
            ha='left', va='top', fontsize=9, fontweight='bold',
            color=stylesheet.COLORS['strat'], alpha=1)

    ax.set_ylim(bottom=0)

    ax.set_xlabel("Time [min]", fontsize=10)
    ax.set_ylabel("Rainfall accumulation [mm/5min]", fontsize=10)
    ax.legend(loc='best', fontsize=8)
    ax.grid(True, linestyle=':', alpha=0.5, linewidth=0.5)

    plt.tight_layout()
    plt.savefig("figures/md_far_stats_comparison.pdf", bbox_inches='tight')
    plt.savefig("figures/md_far_stats_comparison.png", dpi=300, bbox_inches='tight')
    plt.show()
    plt.close(fig)


# ===========================================================================
# MAIN
# ===========================================================================

if __name__ == "__main__":
    generate_qpe_accumulation()
    generate_vpr_plots()
    generate_rainfall_accumulation_graph()
    print("\nAll figures generated successfully.")
