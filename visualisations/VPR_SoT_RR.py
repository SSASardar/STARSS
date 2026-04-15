import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation, FFMpegWriter
from matplotlib.gridspec import GridSpec

# -------------------------
# Load VPR stages
# -------------------------
vpr_file = "outputs/vpr_stages.txt"
vpr_data = np.loadtxt(vpr_file, skiprows=1)

height = vpr_data[:, 0]
vpr_strat  = vpr_data[:, 1]
vpr_growth = vpr_data[:, 2]
vpr_mature = vpr_data[:, 3]
vpr_decay  = vpr_data[:, 4]

# Define the stages and corresponding colors
stages = [(0, 60, 'blue'),    # stage 1: 0-15 min
          (60, 120, 'green'), # stage 2: 15-30 min
          (120, 170, 'orange'),# stage 3: 30-45 min
          (170, 230, 'red')] # stage 4: 45-60 min

# -------------------------
# Load reflectivity profile
# -------------------------
reflectivity_file = "outputs/reflectivity_profile.txt"
reflectivity_data = np.loadtxt(reflectivity_file, skiprows=1)
heights_anim = reflectivity_data[:, 0]
reflectivities = reflectivity_data[:, 1:]  # (n_heights, n_times)
n_heights, n_times = reflectivities.shape

# Extract time labels from header
with open(reflectivity_file, "r") as f:
    header = f.readline().strip().split("\t")[1:]
time_labels = [h[1:] for h in header]  # remove 'T' prefix

# -------------------------
# Compute lowest non-zero reflectivity rainfall rate
# -------------------------
a, b = 200, 1.6  # Marshall–Palmer coefficients
rain_rates = []
for t in range(n_times):
    refl_col = reflectivities[:, t]
    nonzero_mask = refl_col > 0
    if np.any(nonzero_mask):
        first_idx = np.argmax(nonzero_mask)  # first True index
        dBZ_val = refl_col[first_idx]
        Z = 10 ** (dBZ_val / 10.0)
        R = (Z / a) ** (1.0 / b)
    else:
        R = np.nan
    rain_rates.append(R)
rain_rates = np.array(rain_rates)

# -------------------------
# Set up figure
# -------------------------
fig = plt.figure(figsize=(12, 8), constrained_layout=True)
gs = GridSpec(3, 4, height_ratios=[1, 2, 1], figure=fig)

# -------------------------
# Top row: 4 small subplots
# -------------------------
profiles = [vpr_strat, vpr_growth, vpr_mature, vpr_decay]
titles = ['VPR_1', 'VPR_2', 'VPR_3', 'VPR_4']
colors = ['blue', 'green', 'orange', 'red']

axes_top = []
for i in range(4):
    ax = fig.add_subplot(gs[0, i], sharey=axes_top[0] if axes_top else None)
    mask = profiles[i] != 0
    ax.plot(profiles[i][mask], height[mask], color=colors[i])
    ax.set_title(titles[i], fontsize=9)
    ax.set_xlabel('Reflectivity', fontsize=8)
    ax.tick_params(axis='x', rotation=30)
    if i == 0:
        ax.set_ylabel('Height (m)', fontsize=8)
    ax.grid(True)
    axes_top.append(ax)

# -------------------------
# Middle row: animation vertical profile
# -------------------------
ax_anim = fig.add_subplot(gs[1, :])
line, = ax_anim.plot(reflectivities[:, 0], heights_anim, lw=2)
ax_anim.set_xlim(np.nanmin(reflectivities), np.nanmax(reflectivities))
ax_anim.set_ylim(np.min(heights_anim), np.max(heights_anim))
ax_anim.set_xlabel("Reflectivity (dBZ)")
ax_anim.set_ylabel("Height (m)")
ax_anim.set_title(f"Vertical Reflectivity Profile over time")
ax_anim.grid(True)

# -------------------------
# Bottom row: rainfall rate time series
# -------------------------
time_minutes = np.array(time_labels, dtype=float)  # convert to numeric minutes

ax_rain = fig.add_subplot(gs[2, :])
ax_rain.plot(time_minutes, rain_rates, color='purple', lw=2)
dot, = ax_rain.plot(time_minutes[0], rain_rates[0], 'ro', markersize=8)
ax_rain.set_xlim(time_minutes[0], time_minutes[-1])

ax_rain.set_ylim(1, np.nanmax(rain_rates)*1.1)
ax_rain.set_yscale('log')

# Compute min and max ignoring NaNs
rain_min = np.nanmin(rain_rates)
rain_max = np.nanmax(rain_rates)

# Add horizontal dotted lines
ax_rain.axhline(rain_min, color='gray', linestyle=':', alpha=0.6, lw=1)
ax_rain.axhline(rain_max, color='gray', linestyle=':', alpha=0.6, lw=1)
# Add labels underneath lines, just to the right of the y-axis
ax_rain.text(0.05, rain_min * 0.95, f"Min: {rain_min:.2f}", va='top', ha='left',
             transform=ax_rain.transData, fontsize=8, alpha=0.6)
ax_rain.text(0.05, rain_max * 0.95, f"Max: {rain_max:.2f}", va='top', ha='left',
             transform=ax_rain.transData, fontsize=8, alpha=0.6)
ax_rain.set_xlabel("Time (minutes)")
ax_rain.set_ylabel("Rainfall Rate (mm/h)")
ax_rain.grid(True)

rain_text = ax_rain.text(0.98, 0.95, f"R = {rain_rates[0]:.2f} mm/h",
                         transform=ax_rain.transAxes, ha='right', va='top',
                         fontsize=10, bbox=dict(boxstyle="round,pad=0.3", fc="white", ec="gray", alpha=0.8))

# -------------------------
# Animation update function
# -------------------------
def update(frame):
    # Update vertical profile line
    line.set_xdata(reflectivities[:, frame])
    
    # Determine which stage/color we are in
    current_time = time_minutes[frame]
    for start, end, color in stages:
        if start <= current_time < end:
            line.set_color(color)
            break
    else:
        line.set_color('blue')
    
    # Update rainfall rate dot
    dot.set_data([time_minutes[frame]], [rain_rates[frame]])
    
    # Update rainfall text
    if np.isnan(rain_rates[frame]):
        rain_text.set_text("R = NaN")
    else:
        rain_text.set_text(f"R = {rain_rates[frame]:.2f} mm/h")
    
    return line, dot, rain_text

# -------------------------
# Run animation
# -------------------------
ani = FuncAnimation(fig, update, frames=n_times, interval=200, blit=True)
writer = FFMpegWriter(fps=5, codec='h264', bitrate=2000)
ani.save('my_animation.mp4', writer=writer)
plt.show()
