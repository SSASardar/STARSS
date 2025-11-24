import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation, FFMpegWriter
import glob
import os


# -----------------------
# Helper functions
# -----------------------
def load_grid(filename):
    values = []
    with open(filename, "r") as f:
        for line in f:
            if line.startswith("#") or not line.strip():
                continue
            row = [float(tok) if tok.lower() != "nan" else np.nan for tok in line.split()]
            values.append(row)
    return np.array(values)

def pad_grid(grid, target_shape):
    padded = np.full(target_shape, np.nan)
    rows, cols = grid.shape
    padded[:rows, :cols] = grid
    return padded

def downsample(grid, factor=2):
    return grid[::factor, ::factor]


# -----------------------
# Load grid files
# -----------------------
true_files = sorted(glob.glob("outputs/true_g_*.txt"))
true_grids_raw = [load_grid(f) for f in true_files]

max_rows = max(g.shape[0] for g in true_grids_raw)
max_cols = max(g.shape[1] for g in true_grids_raw)

true_grids = [
    downsample(pad_grid(g, (max_rows, max_cols)), factor=2)
    for g in true_grids_raw
]

num_frames = len(true_grids)

vmin = min(np.nanmin(g) for g in true_grids)
vmax = max(np.nanmax(g) for g in true_grids)


# -----------------------
# Load stats (only true rainfall)
# -----------------------
stats = np.loadtxt("outputs/stats.txt", skiprows=1)
scan_id = stats[:, 0]
total_true_mm2 = stats[:, 7]
time = scan_id * 5.0  # minutes


# -----------------------
# Setup figure
# -----------------------
fig = plt.figure(figsize=(12, 4))
gs = fig.add_gridspec(1, 2, width_ratios=[1, 2])

cmapRAD = "cividis"

# --- Reflectivity panel ---
ax_true = fig.add_subplot(gs[0, 0])
im_true = ax_true.imshow(
    true_grids[0],
    cmap=cmapRAD,
    origin="lower",
    vmin=vmin,
    vmax=vmax
)
ax_true.set_title("Refl. at lowest alt. - 0 min")
# Remove ticks + tick labels
ax_true.set_xticks([]); ax_true.set_yticks([])
# Colorbar
true_pos = ax_true.get_position()
cbar_ax = fig.add_axes([
    true_pos.x0 -0.09,
    true_pos.y0,
    0.02,
    true_pos.height
])
cbar = fig.colorbar(im_true, cax=cbar_ax, orientation='vertical')
cbar.set_label("Reflectivity (dBZ)")
cbar.set_ticks(np.linspace(vmin, vmax, 6))
cbar.ax.tick_params(labelsize=10)


# --- Rainfall time-series ---
ax_stats = fig.add_subplot(gs[0, 1])
ax_stats.plot(time, total_true_mm2, color='orange', label='True mm²')
ax_stats.set_title("True rainfall rate over time")
ax_stats.set_xlabel("Time (min)")
ax_stats.set_ylabel("Rainfall rate [mm per sec per m²]")
ax_stats.grid(True)
ax_stats.legend()

time_line = ax_stats.axvline(time[0], color="black", linestyle="--")


# -----------------------
# Update function
# -----------------------
def update(frame):
    timestamp_min = frame * 5

    # update reflectivity grid
    im_true.set_data(true_grids[frame].T)
    ax_true.set_title(f"Refl. at lowest alt. - {timestamp_min} min")

    # update moving vertical line
    time_line.set_xdata([timestamp_min])

    return [im_true, time_line]


# -----------------------
# Animate
# -----------------------
ani = FuncAnimation(fig, update, frames=num_frames, blit=False)

os.makedirs("outputs", exist_ok=True)
writer = FFMpegWriter(fps=5, metadata=dict(artist='Radar Anim'), bitrate=1800)
ani.save("outputs/dashboard_animationB.mp4", writer=writer)

print("Saved animation to outputs/dashboard_animationB.mp4")

