import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation, FFMpegWriter
import glob
import os


# --------------------------------------------------
# Helpers
# --------------------------------------------------

def load_grid(filename):
    values = []
    with open(filename, "r") as f:
        for line in f:
            if line.startswith("#") or not line.strip():
                continue
            row = [
                float(tok) if tok.lower() != "nan"
                else np.nan
                for tok in line.split()
            ]
            values.append(row)
    return np.array(values)


def pad_grid(grid, target_shape):
    padded = np.full(target_shape, np.nan)
    rows, cols = grid.shape
    padded[:rows, :cols] = grid
    return padded


def downsample(grid, factor=2):
    return grid[::factor, ::factor]


# --------------------------------------------------
# Load grid files
# --------------------------------------------------

disp_files = sorted(glob.glob("outputs/disp_g_*.txt"))
ad_disp_files = sorted(glob.glob("outputs/ad_disp_g_*.txt"))
true_files = sorted(glob.glob("outputs/true_g_*.txt"))

disp_raw = [load_grid(f) for f in disp_files]
ad_disp_raw = [load_grid(f) for f in ad_disp_files]
true_raw = [load_grid(f) for f in true_files]

max_rows = max(
    max(g.shape[0] for g in disp_raw),
    max(g.shape[0] for g in ad_disp_raw),
    max(g.shape[0] for g in true_raw)
)

max_cols = max(
    max(g.shape[1] for g in disp_raw),
    max(g.shape[1] for g in ad_disp_raw),
    max(g.shape[1] for g in true_raw)
)

target_shape = (max_rows, max_cols)

disp_grids = [
    downsample(pad_grid(g, target_shape))
    for g in disp_raw
]

ad_disp_grids = [
    downsample(pad_grid(g, target_shape))
    for g in ad_disp_raw
]

true_grids = [
    downsample(pad_grid(g, target_shape))
    for g in true_raw
]

num_frames = min(
    len(disp_grids),
    len(ad_disp_grids),
    len(true_grids)
)

# --------------------------------------------------
# Common colour scale
# --------------------------------------------------

vmin = min(
    np.nanmin(g)
    for g in disp_grids + ad_disp_grids + true_grids
)

vmax = max(
    np.nanmax(g)
    for g in disp_grids + ad_disp_grids + true_grids
)

# --------------------------------------------------
# Load stats
# --------------------------------------------------

stats = np.loadtxt("outputs/stats.txt", skiprows=1)
ad_stats = np.loadtxt("outputs/ad_stats.txt", skiprows=1)

scan_id = stats[:, 0]
time = scan_id * 5.0

measured_mm2 = stats[:, 6]
true_mm2 = stats[:, 7]

adaptive_measured_mm2 = ad_stats[:, 6]

# --------------------------------------------------
# Figure layout
# --------------------------------------------------

fig = plt.figure(figsize=(18, 10))

gs = fig.add_gridspec(
    2,
    3,
    height_ratios=[2, 1],
    hspace=0.3
)

ax_disp = fig.add_subplot(gs[0, 0])
ax_ad = fig.add_subplot(gs[0, 1])
ax_true = fig.add_subplot(gs[0, 2])

ax_stats = fig.add_subplot(gs[1, :])

cmapRAD = "cividis"

# --------------------------------------------------
# Initial images
# --------------------------------------------------

im_disp = ax_disp.imshow(
    disp_grids[0].T,
    cmap=cmapRAD,
    origin="lower",
    vmin=vmin,
    vmax=vmax
)

im_ad = ax_ad.imshow(
    ad_disp_grids[0].T,
    cmap=cmapRAD,
    origin="lower",
    vmin=vmin,
    vmax=vmax
)

im_true = ax_true.imshow(
    true_grids[0].T,
    cmap=cmapRAD,
    origin="lower",
    vmin=vmin,
    vmax=vmax
)

ax_disp.set_title("What the radar sees")
ax_ad.set_title("What the adaptive radar sees")
ax_true.set_title("Refl. at lowest alt.")

# --------------------------------------------------
# Shared colourbar
# --------------------------------------------------

disp_pos = ax_disp.get_position()
true_pos = ax_true.get_position()

cbar_ax = fig.add_axes([
    disp_pos.x0,
    disp_pos.y0 - 0.05,
    true_pos.x1 - disp_pos.x0,
    0.02
])

cbar = fig.colorbar(
    im_disp,
    cax=cbar_ax,
    orientation="horizontal"
)

cbar.set_label("Reflectivity (dBZ)")
cbar.set_ticks(np.linspace(vmin, vmax, 6))

# --------------------------------------------------
# Stats plot
# --------------------------------------------------

ax_stats.plot(
    time,
    measured_mm2,
    marker="o",
    color="purple",
    label="Measured mm²"
)

ax_stats.plot(
    time,
    adaptive_measured_mm2,
    marker="o",
    color="green",
    label="Adaptive measured mm²"
)

ax_stats.plot(
    time,
    true_mm2,
    marker="o",
    color="orange",
    label="True mm²"
)

ax_stats.set_title("True vs Measured over time")
ax_stats.set_xlabel("Time (min)")
ax_stats.set_ylabel("Rainfall Accumulation \n[mm per 5 mins per unit area]")
ax_stats.grid(True)
ax_stats.legend()

time_line = ax_stats.axvline(
    time[0],
    color="black",
    linestyle="--"
)

# --------------------------------------------------
# Animation update
# --------------------------------------------------

def update(frame):

    timestamp_min = frame * 5

    im_disp.set_data(disp_grids[frame].T)
    im_ad.set_data(ad_disp_grids[frame].T)
    im_true.set_data(true_grids[frame].T)

    ax_disp.set_title(
        f"What the radar sees - {timestamp_min} min"
    )

    ax_ad.set_title(
        f"What the adaptive radar sees - {timestamp_min} min"
    )

    ax_true.set_title(
        f"Refl. at lowest alt. - {timestamp_min} min"
    )

    time_line.set_xdata([timestamp_min])

    return [
        im_disp,
        im_ad,
        im_true,
        time_line
    ]


# --------------------------------------------------
# Animate
# --------------------------------------------------

ani = FuncAnimation(
    fig,
    update,
    frames=num_frames,
    interval=200,
    blit=False
)

# --------------------------------------------------
# Save
# --------------------------------------------------

os.makedirs("outputs", exist_ok=True)

writer = FFMpegWriter(
    fps=5,
    metadata=dict(artist="Radar Anim"),
    bitrate=1800
)

ani.save(
    "outputs/AAFIGUREadaptive_comparison_dashboard.mp4",
    writer=writer
)

print(
    "Saved animation to outputs/AAFIGUREadaptive_comparison_dashboard.mp4"
)
