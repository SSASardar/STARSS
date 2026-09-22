import numpy as np
import matplotlib.pyplot as plt
import stylesheet  # centralised stylesheet

# ===========================
# 1. HELPER FUNCTIONS
# ===========================
def load_vpr_file_emp(filename, timestep=39):
    """
    Load a VPR file and extract a specific timestep.
    
    Parameters
    ----------
    filename : str
        Path to the VPR file
    timestep : int
        The timestep index to extract (0-based)
    
    Returns
    -------
    heights : numpy.ndarray
        Array of heights in km
    reflectivity : numpy.ndarray
        Array of reflectivity values in dBZ
    """
    with open(filename, 'r') as f:
        lines = f.readlines()
    
    # Find all timesteps (separated by empty lines)
    timesteps = []
    current_timestep = []
    
    for line in lines:
        line = line.strip()
        if not line:  # Empty line = separator
            if current_timestep:
                timesteps.append(current_timestep)
                current_timestep = []
        elif line.startswith('#'):
            continue  # Skip comments
        else:
            current_timestep.append(line)
    
    # Add the last timestep if it exists
    if current_timestep:
        timesteps.append(current_timestep)
    
    # Check if the requested timestep exists
    if timestep >= len(timesteps):
        print(f"Warning: Only {len(timesteps)} timesteps available. Using last timestep.")
        timestep = -1  # Use the last one
    
    # Parse the requested timestep
    data = timesteps[timestep]
    heights = []
    reflectivity = []
    
    for line in data:
        parts = line.split()
        if len(parts) >= 5:
            bin_idx = int(parts[0])
            height = float(parts[1])
            refl = float(parts[3])
            heights.append(height)
            reflectivity.append(refl)
    
    return np.array(heights), np.array(reflectivity)


def load_vpr_file_true(filename, timestep=39):
    """
    Load a VPR file and extract a specific timestep.
    
    Parameters
    ----------
    filename : str
        Path to the VPR file
    timestep : int
        The timestep index to extract (0-based)
    
    Returns
    -------
    heights : numpy.ndarray
        Array of heights in km
    reflectivity : numpy.ndarray
        Array of reflectivity values in dBZ
    """
    with open(filename, 'r') as f:
        lines = f.readlines()
    
    # Find all timesteps (separated by empty lines)
    timesteps = []
    current_timestep = []
    
    for line in lines:
        line = line.strip()
        if not line:  # Empty line = separator
            if current_timestep:
                timesteps.append(current_timestep)
                current_timestep = []
        elif line.startswith('#'):
            continue  # Skip comments
        else:
            current_timestep.append(line)
    
    # Add the last timestep if it exists
    if current_timestep:
        timesteps.append(current_timestep)
    
    # Check if the requested timestep exists
    if timestep >= len(timesteps):
        print(f"Warning: Only {len(timesteps)} timesteps available. Using last timestep.")
        timestep = -1  # Use the last one
    
    # Parse the requested timestep
    data = timesteps[timestep]
    heights = []
    reflectivity = []
    
    for line in data:
        parts = line.split()
        if len(parts) >= 3:
            bin_idx = int(parts[0])
            height = float(parts[1])
            refl = float(parts[2])
            heights.append(height)
            reflectivity.append(refl)
    
    return np.array(heights), np.array(reflectivity)

# ===========================
# 2. LOAD DATA (39th timestep)
# ===========================

TIMESTEP = 39

# Load stratiform data
heights_strat_true, refl_strat_true = load_vpr_file_true("outputs/vpr_true_strat.txt", TIMESTEP)
heights_strat_emp, refl_strat_emp = load_vpr_file_emp("outputs/vpr_emp_strat_rhi.txt", TIMESTEP)
heights_strat_emp_C, refl_strat_emp_C = load_vpr_file_emp("outputs/vpr_emp_strat_C.txt", TIMESTEP)
heights_strat_emp_X, refl_strat_emp_X = load_vpr_file_emp("outputs/vpr_emp_strat_X.txt", TIMESTEP)
# Load convective data
heights_conv_true, refl_conv_true = load_vpr_file_true("outputs/vpr_true_conv.txt", TIMESTEP)
heights_conv_emp, refl_conv_emp = load_vpr_file_emp("outputs/vpr_emp_conv_rhi.txt", TIMESTEP)
heights_conv_emp_C, refl_conv_emp_C = load_vpr_file_emp("outputs/vpr_emp_conv_C.txt", TIMESTEP)
heights_conv_emp_X, refl_conv_emp_X = load_vpr_file_emp("outputs/vpr_emp_conv_X.txt", TIMESTEP)

# ===========================
# 3. HELPER FUNCTION TO CREATE INDIVIDUAL FIGURE
# ===========================

def create_vpr_figure(heights_true, refl_true,
                      heights_emp, refl_emp,
                      heights_emp_C, refl_emp_C,
                      heights_emp_X, refl_emp_X,
                      filename,
                      inset_xlim, inset_ylim):
    """Create a single VPR comparison figure with an inset in the bottom-left corner."""
    fig, ax = plt.subplots(figsize=(6, 6))

    # True - solid line
    ax.plot(refl_true[0:18], heights_true[0:18],
            color=stylesheet.COLORS['black'],
            linestyle='-',
            linewidth=1,
            markersize=3,
            label='True')

    # Empirical C-band - dash-dot with triangles
    ax.plot(refl_emp_C[0:18], heights_emp_C[0:18],
            color=stylesheet.COLORS['black'],
            linestyle='-.',
            linewidth=1,
            marker='^',
            markersize=3,
            label='PPI-based (C-band)')

    # Empirical X-band - dash-dot with circles
    ax.plot(refl_emp_X[0:18], heights_emp_X[0:18],
            color=stylesheet.COLORS['black'],
            linestyle='-.',
            linewidth=1,
            marker='o',
            markersize=3,
            label='PPI-based (X-band)')

    # Empirical RHI - dotted with circles
    ax.plot(refl_emp[0:18], heights_emp[0:18],
            color=stylesheet.COLORS['black'],
            linestyle=':',
            linewidth=1,
            marker='o',
            markersize=3,
            label='RHI-based (X-band)')

    ax.set_xlabel("Reflectivity [dBZ]", fontsize=10)
    ax.set_ylabel("Height [km]", fontsize=10)
    ax.legend(loc='best', fontsize=11)
    ax.grid(True, linestyle=':', alpha=0.5, linewidth=0.5)

    # Style cleanup: hide spines
    for s in ['top', 'right']:
        ax.spines[s].set_visible(False)

    # ===========================
    # INSET: first 9 data points, bottom-left corner
    # ===========================
    ax_inset = ax.inset_axes([0.075, 0.075, 0.5, 0.5])  # [left, bottom, width, height] in axes fraction

    # Replot the first 9 points in the inset
    ax_inset.plot(refl_true[0:8], heights_true[0:8],
                  color=stylesheet.COLORS['black'],
                  linestyle='-', linewidth=1, markersize=3)

    ax_inset.plot(refl_emp_C[0:8], heights_emp_C[0:8],
                  color=stylesheet.COLORS['black'],
                  linestyle='-.', linewidth=1, marker='^', markersize=3)

    ax_inset.plot(refl_emp_X[0:8], heights_emp_X[0:8],
                  color=stylesheet.COLORS['black'],
                  linestyle='-.', linewidth=1, marker='o', markersize=3)

    ax_inset.plot(refl_emp[0:8], heights_emp[0:8],
                  color=stylesheet.COLORS['black'],
                  linestyle=':', linewidth=1, marker='o', markersize=3)

    # Set the inset limits as requested
    ax_inset.set_xlim(inset_xlim[0], inset_xlim[1])
    ax_inset.set_ylim(inset_ylim[0], inset_ylim[1])
    ax_inset.grid(True, linestyle=':', alpha=0.4, linewidth=0.4)
    ax_inset.tick_params(labelsize=7)

    # Save high-res outputs
    plt.savefig(f"{filename}.png", dpi=300, bbox_inches='tight')
    plt.savefig(f"{filename}.pdf", bbox_inches='tight')
    plt.show()
    plt.close(fig)


# ===========================
# 4. CREATE THE TWO FIGURES
# ===========================

# Stratiform: inset shows reflectivity 25–45 dBZ, height 0–5 km
create_vpr_figure(heights_strat_true, refl_strat_true,
                  heights_strat_emp, refl_strat_emp,
                  heights_strat_emp_C, refl_strat_emp_C,
                  heights_strat_emp_X, refl_strat_emp_X,
                  "figures/md_vpr_stratiform",
                  inset_xlim=(26, 40), inset_ylim=(0, 4))

# Convective: inset shows reflectivity 30–50 dBZ, height 0–5 km
create_vpr_figure(heights_conv_true, refl_conv_true,
                  heights_conv_emp, refl_conv_emp,
                  heights_conv_emp_C, refl_conv_emp_C,
                  heights_conv_emp_X, refl_conv_emp_X,
                  "figures/md_vpr_convective",
                  inset_xlim=(43, 50), inset_ylim=(0, 4))

# ===========================
# 5. PRINT SUMMARY
# ===========================

print(f"VPR Comparison - Timestep {TIMESTEP}")
print("=" * 50)
print(f"Stratiform:")
print(f"  True VPR points: {len(heights_strat_true)}")
print(f"  Empirical VPR points: {len(heights_strat_emp)}")
print(f"Convective:")
print(f"  True VPR points: {len(heights_conv_true)}")
print(f"  Empirical VPR points: {len(heights_conv_emp)}")
