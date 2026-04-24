import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation, FFMpegWriter
import glob
import os
import re
from scipy.interpolate import interp1d


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

def load_VPR(filename):
    refl, height = [], []
    with open(filename, "r") as f:
        for line in f:
            if line.startswith("#") or not line.strip():
                continue
            parts = line.split()
            if len(parts) >= 3:
                r, h = float(parts[1]), float(parts[2])
                refl.append(r)
                height.append(h)
    return np.array(refl), np.array(height)

def load_point_profile(filename):
    refl, height = [], []
    with open(filename, "r") as f:
        for line in f:
            if line.startswith("#") or not line.strip():
                continue
            parts = line.split()
            if len(parts) >= 3:
                refl.append(float(parts[1]))
                height.append(float(parts[2]))
    return np.array(refl), np.array(height)

# --- radar scan parsing helpers ---
key_value_re = re.compile(r'(\w+(?:\.\w+)*)=([\w\.\-]+)')

def parse_scan_block(lines):
    meta, data = {}, []
    grid_data_accum, reading_grid_data = [], False
    for line in lines:
        line = line.strip()
        if not line or line.startswith("==="):
            continue
        if reading_grid_data:
            if key_value_re.match(line):
                reading_grid_data = False
                data = list(map(float, " ".join(grid_data_accum).split()))
            else:
                grid_data_accum.append(line)
                continue
        if line.startswith("grid.data="):
            reading_grid_data = True
            grid_data_accum.append(line[len("grid.data="):].strip())
            continue
        if not reading_grid_data:
            match = key_value_re.match(line)
            if match:
                key, val = match.groups()
                try:
                    meta[key] = float(val)
                except ValueError:
                    meta[key] = val
    if reading_grid_data:
        data = list(map(float, " ".join(grid_data_accum).split()))
    num_ranges = int(meta.get('box.num_ranges', 0))
    num_angles = int(meta.get('box.num_angles', 0))
    data_array = np.array(data).reshape((num_ranges, num_angles))
    return meta, data_array

def load_second_scan(filename):
    with open(filename, 'r') as f:
        lines = f.readlines()
    scans, inside, current = [], False, []
    for line in lines:
        if "=== BEGIN RADAR_SCAN ===" in line:
            inside, current = True, []
        elif "=== END RADAR_SCAN ===" in line:
            inside = False
            scans.append(current)
        elif inside:
            current.append(line)
    for block in scans:
        meta, data = parse_scan_block(block)
        if int(meta.get('scan.index', -1)) == 1:
            return meta, data
    return None, None

# -----------------------
# Load grid files
# -----------------------
disp_files = sorted(glob.glob("outputs/disp_g_*.txt"))
true_files = sorted(glob.glob("outputs/true_g_*.txt"))
point_files = sorted(glob.glob("outputs/heights_point_*.txt"))
vpr_files   = sorted(glob.glob("outputs/VPR_conv_*.txt"))
radar_files = sorted(glob.glob("outputs/radar_scan_*.txt"))

disp_grids_raw = [load_grid(f) for f in disp_files]
true_grids_raw = [load_grid(f) for f in true_files]

max_rows = max(max(g.shape[0] for g in disp_grids_raw),
               max(g.shape[0] for g in true_grids_raw))
max_cols = max(max(g.shape[1] for g in disp_grids_raw),
               max(g.shape[1] for g in true_grids_raw))

disp_grids = [downsample(pad_grid(g, (max_rows, max_cols)), factor=2) for g in disp_grids_raw]
true_grids = [downsample(pad_grid(g, (max_rows, max_cols)), factor=2) for g in true_grids_raw]

num_frames = len(disp_grids)

vmin = min(np.nanmin(g) for g in disp_grids + true_grids)
vmax = max(np.nanmax(g) for g in disp_grids + true_grids)

# -----------------------
# Load stats
# -----------------------
stats = np.loadtxt("outputs/stats.txt", skiprows=1)
scan_id = stats[:, 0]
MSE = stats[:, 1]
MAE = stats[:, 2]
Bias = stats[:, 3]
total_measured_mm2 = stats[:, 6]
total_true_mm2 = stats[:, 7]
time = scan_id * 5.0  # minutes

# -----------------------
# Load radar scans (scan.index==1)
# -----------------------
radar_scans = []
for f in radar_files:
    meta, data = load_second_scan(f)
    if data is not None:
        radar_scans.append((meta, data))

radar_vmin = min(np.nanmin(d) for _, d in radar_scans)
radar_vmax = max(np.nanmax(d) for _, d in radar_scans)

# -----------------------
# Setup figure
# -----------------------
fig = plt.figure(figsize=(16, 10))
gs = fig.add_gridspec(2, 3, height_ratios=[2, 1])


cmapRAD = "cividis"

ax_vpr = fig.add_subplot(gs[0, 0])
ax_disp = fig.add_subplot(gs[0, 1])
ax_true = fig.add_subplot(gs[0, 2])
ax_radar = fig.add_subplot(gs[1, 0], projection="polar")
ax_stats = fig.add_subplot(gs[1, 1:])

im_disp = ax_disp.imshow(disp_grids[0], cmap=cmapRAD, origin="lower", vmin=vmin, vmax=vmax)
im_true = ax_true.imshow(true_grids[0], cmap=cmapRAD, origin="lower", vmin=vmin, vmax=vmax)

ax_disp.set_title("What the radar sees")
ax_true.set_title("Refl. at lowest alt.")

# Colorbar for disp/true

disp_pos = ax_disp.get_position()
true_pos = ax_true.get_position()
cbar_ax = fig.add_axes([disp_pos.x0, disp_pos.y0 - 0.05, true_pos.x1 - disp_pos.x0, 0.02])
cbar = fig.colorbar(im_disp, cax=cbar_ax, orientation='horizontal')
cbar.set_label("Reflectivity (dBZ)")
cbar.set_ticks(np.linspace(vmin, vmax, 6))
cbar.ax.tick_params(labelsize=10)

# Stats plot
ax_stats.plot(time, total_measured_mm2, marker='o', color='purple', label='Measured mm²')
ax_stats.plot(time, total_true_mm2, marker='o', color='orange', label='True mm²')
ax_stats.set_title("True vs Measured over time")
ax_stats.set_xlabel("Time (min)")
ax_stats.set_ylabel("Rainfall rate [mm per sec per m²]")
ax_stats.legend()
ax_stats.grid(True)
time_line = ax_stats.axvline(time[0], color="black", linestyle="--")

# VPR plots
vpr_line, = ax_vpr.plot([], [], '-', color="red", label="VPR conv")
vpr_scatter = ax_vpr.scatter([], [], color='red')
profile_lines = []
ax_vpr.set_xlim(-10, 60)
ax_vpr.set_ylim(0, 25000)
ax_vpr.set_xlabel("Reflectivity")
ax_vpr.set_ylabel("Height")
ax_vpr.legend()
ax_vpr.set_title("What radar measures at (x,y)=(450,300)")

# Preplot stratiform VPR for scan 0000
refl_s, h_s = load_VPR("outputs/VPR_strat_0000.txt")
if len(refl_s) > 1:
    f_s = interp1d(h_s, refl_s, kind="linear", fill_value="extrapolate")
    h_new_s = np.linspace(min(h_s), max(h_s), 100)
    refl_new_s = f_s(h_new_s)
    ax_vpr.plot(refl_new_s, h_new_s, 'g-', label='VPR strat')
    ax_vpr.legend()

# Radar polar initial plot
meta0, data0 = radar_scans[0]
r_res = meta0.get('box.range_resolution', 1)
min_r = meta0.get('box.min_range_gate', 0) * r_res
r = min_r + np.arange(data0.shape[0]) * r_res
theta = np.deg2rad((meta0.get('box.min_angle', 0) + np.arange(data0.shape[1])) *
                   meta0.get('box.angular_resolution', 1))
R, Theta = np.meshgrid(r, theta, indexing='ij')

radar_pcol = None
ax_radar.set_ylim(0, meta0.get('radar.maximum_range', r[-1]))

# -----------------------
# Update function
# -----------------------

radar_pcol = None  # will hold the current pcolormesh

def update(frame):
    # Grids
    im_disp.set_data(disp_grids[frame].T)
    im_true.set_data(true_grids[frame].T)
    timestamp_min = frame * 5
    ax_disp.set_title(f"What the radar sees - {timestamp_min} min")
    ax_true.set_title(f"Refl. at lowest alt. - {timestamp_min} min")

    # Remove old profile lines
    for obj in profile_lines:
        obj.remove()
    profile_lines.clear()

    _, h_p = load_point_profile(point_files[frame])
    for h in h_p:
        line, = ax_vpr.plot([-10, 60], [h, h], 'b--', alpha=0.6)
        profile_lines.append(line)

    refl_v, h_v = load_VPR(vpr_files[frame])
    if len(refl_v) > 1:
        f = interp1d(h_v, refl_v, kind="linear", fill_value="extrapolate")
        h_new = np.linspace(min(h_v), max(h_v), 100)
        refl_new = f(h_new)
        vpr_line.set_data(refl_new, h_new)
        vpr_scatter.set_offsets(np.c_[refl_v, h_v])

    time_line.set_xdata([timestamp_min])

    # Radar scan
    global radar_pcol  # so we can reassign

    if frame < len(radar_scans):
        meta, data = radar_scans[frame]
        r_res = meta.get('box.range_resolution', 1)
        min_r = meta.get('box.min_range_gate', 0) * r_res
        r = min_r + np.arange(data.shape[0]) * r_res
        theta = np.deg2rad((meta.get('box.min_angle', 0) + np.arange(data.shape[1])) *
                           meta.get('box.angular_resolution', 1))
        R, Theta = np.meshgrid(r, theta, indexing='ij')
    
        # Remove old pcolormesh safely
        if radar_pcol is not None:
            radar_pcol.remove()

        # Draw new pcolormesh
        radar_pcol = ax_radar.pcolormesh(
            Theta, R, data, shading='auto', cmap=cmapRAD,
            vmin=radar_vmin, vmax=radar_vmax
        )

        ax_radar.set_ylim(0, meta.get('radar.maximum_range', r[-1]))
        # Only show the max range label
        max_range = r[-1]
        ax_radar.set_yticks([max_range])               # place tick only at max range
        ax_radar.set_yticklabels([f"{max_range/1000:.0f} km"])  # label it

    return [im_disp, im_true, vpr_line, vpr_scatter, time_line,
            radar_pcol] + profile_lines


# -----------------------
# Animate
# -----------------------
ani = FuncAnimation(fig, update, frames=num_frames, blit=False)
os.makedirs("outputs", exist_ok=True)
writer = FFMpegWriter(fps=5, metadata=dict(artist='Radar Anim'), bitrate=1800)
ani.save("outputs/dashboard_animationB.mp4", writer=writer)
print("Saved animation to outputs/dashboard_animationB.mp4")
