import numpy as np
import matplotlib.pyplot as plt
import stylesheet  # centralised stylesheet

# ===========================
# 1. LOAD DATA
# ===========================

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

# ===========================
# 2. CREATE FIGURE (3x wider than tall)
# ===========================

fig, ax = plt.subplots(figsize=(12, 4))

# ===========================
# 3. PLOT DATA
# ===========================


# Dataset - True
ax.plot(time_C, total_true_mm2_C, 
        # marker='o', 
        color=stylesheet.COLORS['black'], 
        label='True',
        linewidth=1,
        markersize=3)
        #linestyle = '--')




# Dataset C - Measured
ax.plot(time_C, total_measured_mm2_C, 
        marker='^', 
        color=stylesheet.COLORS['black'], 
        label='Measured (C-band)',
        linewidth=1,
        markersize=3,
        linestyle = '-.')

# Dataset X - Measured
ax.plot(time_X, total_measured_mm2_X, 
        marker='o', 
        color=stylesheet.COLORS['black'], 
        label='Measured (X-band)',
        linewidth=1,
        markersize=3,
        linestyle='-.')
# ===========================
# 4. SET X-AXIS TO START AT ZERO
# ===========================

ax.set_xlim(left=0)

# ===========================
# 5. VERTICAL LINES
# ===========================

# Define time points for vertical lines
t1, t2, t3, t4, t5 = 60, 120, 170, 200, 230

# Add vertical lines (dashed, thin, semi-transparent)
ax.axvline(t1, color='black', linestyle='--', linewidth=0.8, alpha=0.7)
ax.axvline(t2, color='black', linestyle='--', linewidth=0.8, alpha=0.7)
ax.axvline(t3, color='black', linestyle='--', linewidth=0.8, alpha=0.7)
# ax.axvline(t4, color='black', linestyle='--', linewidth=0.8, alpha=0.7)  # Commented out
ax.axvline(t5, color='black', linestyle='--', linewidth=0.8, alpha=0.7)

# ===========================
# 6. SHADED REGIONS
# ===========================

# Get x-axis and y-axis limits for shading
xmin, xmax = ax.get_xlim()
ymin, ymax = ax.get_ylim()
y_range = ymax - ymin

# UNINITIATED region (0 to 60 min) - gray
ax.axvspan(0, t1, alpha=0.15, color=stylesheet.COLORS['strat'], label='_nolegend_')
ax.text(0.05 * t1, ymax - 0.05 * y_range, 'UNINITIATED', 
        ha='left', va='top', fontsize=9, fontweight='bold', 
        color=stylesheet.COLORS['strat'], alpha=1)

# GROWTH region (60 to 120 min) - green
ax.axvspan(t1, t2, alpha=0.15, color=stylesheet.COLORS['growth'], label='_nolegend_')
ax.text(t1 + 0.05 * (t2 - t1), ymax - 0.05 * y_range, 'GROWTH', 
        ha='left', va='top', fontsize=9, fontweight='bold', 
        color=stylesheet.COLORS['growth'], alpha=1)

# MATURE region (120 to 170 min) - blue
ax.axvspan(t2, t3, alpha=0.15, color=stylesheet.COLORS['mature'], label='_nolegend_')
ax.text(t2 + 0.05 * (t3 - t2), ymax - 0.05 * y_range, 'MATURE', 
        ha='left', va='top', fontsize=9, fontweight='bold', 
        color=stylesheet.COLORS['mature'], alpha=1)

# DECAY region (170 to 230 min) - red
ax.axvspan(t3, t5, alpha=0.15, color=stylesheet.COLORS['decay'], label='_nolegend_')
ax.text(t3 + 0.05 * (t5 - t3), ymax - 0.05 * y_range, 'DECAY', 
        ha='left', va='top', fontsize=9, fontweight='bold', 
        color=stylesheet.COLORS['decay'], alpha=1)

# POST-DECAY region (after 230 min) - same as UNINITIATED (gray)
ax.axvspan(t5, xmax, alpha=0.15, color=stylesheet.COLORS['strat'], label='_nolegend_')
ax.text(t5 + 0.05 * (xmax - t5), ymax - 0.05 * y_range, '', 
        ha='left', va='top', fontsize=9, fontweight='bold', 
        color=stylesheet.COLORS['strat'], alpha=1)

# ===========================
# 7. SET Y-AXIS TO START AT ZERO
# ===========================

ax.set_ylim(bottom=0)

# ===========================
# 8. LABELS AND TITLES
# ===========================

#ax.set_title("Rainfall accumulation from raincell", fontsize=11)
ax.set_xlabel("Time [min]", fontsize=10)
ax.set_ylabel("Rainfall accumulation [mm/5min]", fontsize=10)
ax.legend(loc='best', fontsize=8)
ax.grid(True, linestyle=':', alpha=0.5, linewidth=0.5)

# ===========================
# 9. SAVE FIGURE
# ===========================

plt.tight_layout()
plt.savefig("md_stats_comparison.pdf", bbox_inches='tight')
plt.savefig("md_stats_comparison.png", dpi=300, bbox_inches='tight')
plt.show()
