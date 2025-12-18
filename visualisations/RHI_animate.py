import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation, FFMpegWriter
import os
import glob

# ---------------------------------------------------------
# Function to load ONE scan file and return a 2D grid
# ---------------------------------------------------------
def load_scan(filename):
    grid_data = None
    n_angles = None
    n_ranges = None

    with open(filename, "r") as f:
        inside_scan = False
        for line in f:
            line = line.strip()

            if line.startswith("=== BEGIN RADAR_SCAN"):
                inside_scan = True
                continue

            if line.startswith("=== END RADAR_SCAN"):
                break

            if inside_scan:
                if line.startswith("box.num_angles="):
                    n_angles = int(line.split("=")[1])
                if line.startswith("box.num_ranges="):
                    n_ranges = int(line.split("=")[1])

                if line.startswith("grid.data="):
                    data_str = line.split("=", 1)[1]
                    values = data_str.split()
                    while len(values) < n_angles * n_ranges:
                        values.extend(next(f).strip().split())
                    grid_data = np.array(values, dtype=float)[: n_angles * n_ranges]

    # reshape to 2D
    grid = grid_data.reshape((n_ranges, n_angles), order="C")
    #grid = np.transpose(np.fliplr(np.flipud(grid)));
    grid = np.transpose(grid);
    #grid1 = np.rot90(grid,k=-1)
    return grid


# ---------------------------------------------------------
# Load ALL scan files
# ---------------------------------------------------------
files = sorted(glob.glob("outputs/radar_scan_*.txt"))
print(f"Found {len(files)} scan files.")

grids = [load_scan(f) for f in files]
num_frames = len(grids)

## ---------------------------------------------------------
## Setup animation figure
## ---------------------------------------------------------
#fig, ax = plt.subplots(figsize=(10, 6))
#im = ax.imshow(grids[0], aspect="auto", origin="lower", cmap="turbo")
#cbar = plt.colorbar(im, ax=ax, label="Reflectivity dBZ")
#
#ax.set_title("Radar Scan 0")
#
## ---------------------------------------------------------
## Update function for animation
## ---------------------------------------------------------
#def update(frame):
#    im.set_data(grids[frame])
#    ax.set_title(f"Radar Scan {frame:04d}")
#    return [im]
#
#
#
#
#





# ---------------------------------------------------------
# Setup animation figure WITH correct axes
# ---------------------------------------------------------
fig, ax = plt.subplots(figsize=(10, 6))

# Grid dimensions
n_ranges, n_angles = grids[0].shape

im = ax.imshow(
    grids[0],
    origin="lower",
    aspect="auto",
    cmap="turbo",
    extent=(0, n_angles - 1, 0, n_ranges - 1)
)

cbar = plt.colorbar(im, ax=ax, label="Reflectivity (dBZ)")

ax.set_xlabel("Range Gate Index")
ax.set_ylabel("Angle Index")
ax.set_xlim(0, n_ranges - 1)
ax.set_ylim(0, n_angles - 1)
ax.set_title("Radar Scan 0000")

# ---------------------------------------------------------
# Update function for animation WITH axis enforcement
# ---------------------------------------------------------
def update(frame):
    im.set_data(grids[frame])
    ax.set_xlim(0, n_angles - 1)
    ax.set_ylim(0, n_ranges - 1)
    ax.set_title(f"Radar Scan {frame:04d}")
    return [im]






































# ---------------------------------------------------------
# Animate and save to MP4
# ---------------------------------------------------------
ani = FuncAnimation(fig, update, frames=num_frames, blit=False)

os.makedirs("outputs", exist_ok=True)
writer = FFMpegWriter(fps=5, metadata=dict(artist='Radar Anim'), bitrate=1800)

output_file = "outputs/radar_animation.mp4"
ani.save(output_file, writer=writer)

print(f"Saved animation to {output_file}")

