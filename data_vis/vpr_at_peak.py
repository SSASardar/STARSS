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
# 3. CREATE FIGURE WITH 2 SUBPLOTS
# ===========================

fig, axes = plt.subplots(1, 2, figsize=(12, 6), sharey = True)

# ===========================
# 4. PLOT STRATIFORM (Left)
# ===========================

ax = axes[0]

# True - solid line with markers (height vs reflectivity)
ax.plot(refl_strat_true[0:18], heights_strat_true[0:18], 
        color=stylesheet.COLORS['black'],
        linestyle='-',
        linewidth=1,
        markersize=3,
        label='True')

# Empirical - dotted line with markers
ax.plot(refl_strat_emp_C[0:18], heights_strat_emp_C[0:18], 
        color=stylesheet.COLORS['black'],
        linestyle='-.',
        linewidth=1,
        marker='^',
        markersize=3,
        label='PPI-based (C-band)')


# Empirical - dotted line with markers
ax.plot(refl_strat_emp_X[0:18], heights_strat_emp_X[0:18], 
        color=stylesheet.COLORS['black'],
        linestyle='-.',
        linewidth=1,
        marker='o',
        markersize=3,
        label='PPI-based (X-band)')


# Empirical - dotted line with markers
ax.plot(refl_strat_emp[0:18], heights_strat_emp[0:18], 
        color=stylesheet.COLORS['black'],
        linestyle=':',
        linewidth=1,
        marker='o',
        markersize=3,
        label='RHI-based (X-band)')


ax.set_title("Stratiform VPR", fontsize=11)
ax.set_xlabel("Reflectivity [dBZ]", fontsize=10)
ax.set_ylabel("Height [km]", fontsize=10)
ax.legend(loc='best', fontsize=8)
ax.grid(True, linestyle=':', alpha=0.5, linewidth=0.5)

# ===========================
# 5. PLOT CONVECTIVE (Right)
# ===========================

ax = axes[1]

# True - solid line with markers
ax.plot(refl_conv_true[0:18], heights_conv_true[0:18], 
        color=stylesheet.COLORS['black'],
        linestyle='-',
        linewidth=1,
        markersize=3,
        label='True')

# Empirical - dotted line with markers
ax.plot(refl_conv_emp_C[0:18], heights_conv_emp_C[0:18], 
        color=stylesheet.COLORS['black'],
        linestyle='-.',
        linewidth=1,
        marker='^',
        markersize=3,
        label='PPI-based (C-band)')

# Empirical - dotted line with markers
ax.plot(refl_conv_emp_X[0:18], heights_conv_emp_X[0:18], 
        color=stylesheet.COLORS['black'],
        linestyle='-.',
        linewidth=1,
        marker='o',
        markersize=3,
        label='PPI-based (X-band)')

# Empirical - dotted line with markers
ax.plot(refl_conv_emp[0:18], heights_conv_emp[0:18], 
        color=stylesheet.COLORS['black'],
        linestyle=':',
        linewidth=1,
        marker='o',
        markersize=3,
        label='RHI-based (X-band)')



ax.set_title("Convective VPR", fontsize=11)
ax.set_xlabel("Reflectivity [dBZ]", fontsize=10)
#ax.set_ylabel("Height [km]", fontsize=10)
ax.legend(loc='best', fontsize=8)
ax.grid(True, linestyle=':', alpha=0.5, linewidth=0.5)

# ===========================
# 6. APPLY STYLESHEET SETTINGS
# ===========================

for ax in axes:
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)

# ===========================
# 7. SAVE FIGURE
# ===========================

plt.tight_layout()
plt.savefig("md_vpr_comparison.pdf", bbox_inches='tight')
plt.savefig("md_vpr_comparison.png", dpi=300, bbox_inches='tight')
plt.show()

# ===========================
# 8. PRINT SUMMARY
# ===========================

print(f"VPR Comparison - Timestep {TIMESTEP}")
print("=" * 50)
print(f"Stratiform:")
print(f"  True VPR points: {len(heights_strat_true)}")
print(f"  Empirical VPR points: {len(heights_strat_emp)}")
print(f"Convective:")
print(f"  True VPR points: {len(heights_conv_true)}")
print(f"  Empirical VPR points: {len(heights_conv_emp)}")
