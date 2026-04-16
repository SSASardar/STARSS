import os
import glob
import re
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation, FFMpegWriter

# ------------------------------------------------------------
# File handling
# ------------------------------------------------------------
def list_output_files(folder="outputs"):
    #pattern = os.path.join(folder, "*cartesian_grid*.txt")
    pattern = os.path.join(folder, "disp_g*.txt")
    return glob.glob(pattern)

def extract_index(filename):
    basename = os.path.basename(filename)
    match = re.search(r"(\d+)(?=\.txt$)", basename)
    if not match:
        raise ValueError(f"No numeric index in filename: {basename}")
    return int(match.group(1))

def load_grid_from_file(filename):
    with open(filename, 'r') as f:
        return np.array([list(map(float, line.split())) for line in f])

# ------------------------------------------------------------
# Bottom-right anchoring onto dynamic canvas
# ------------------------------------------------------------
def pad_bottom_right(grid, canvas_shape):
    """
    Places grid on a canvas so that bottom-right corner is fixed.
    """
    canvas = np.full(canvas_shape, np.nan)

    r, c = grid.shape
    cr, cc = canvas_shape

    start_row = cr - r
    start_col = cc - c

    canvas[start_row:cr, start_col:cc] = grid
    return canvas

# ------------------------------------------------------------
# Main animation logic
# ------------------------------------------------------------
if __name__ == "__main__":

    files = list_output_files()
    if not files:
        raise RuntimeError("No output files found")

    # ---- Sort numerically ----
    file_index_pairs = [(extract_index(f), f) for f in files]
    file_index_pairs.sort(key=lambda x: x[0])

    # ---- Load grids & find max shape ----
    raw_grids = []
    indices = []
    max_rows = 0
    max_cols = 0

    for idx, f in file_index_pairs:
        g = load_grid_from_file(f)
        raw_grids.append(g)
        indices.append(idx)
        max_rows = max(max_rows, g.shape[0])
        max_cols = max(max_cols, g.shape[1])

    canvas_shape = (max_rows, max_cols)
    print(f"Canvas size: {canvas_shape}")

    # ---- Anchor grids to bottom-right ----
    grids = np.array([
        pad_bottom_right(g, canvas_shape) for g in raw_grids
    ])

    # ---- Global color scale ----
    #vmin = np.nanmin(grids)
    #vmax = np.nanmax(grids)
    vmin = 0
    vmax = 90


    # ---- Figure setup ----
    fig, ax = plt.subplots(figsize=(8, 5))


    # Physical grid spacing (meters)
    dx = 0.025
    dz = 0.025

    nx = canvas_shape[1]   # number of x columns
    nz = canvas_shape[0]   # number of z rows
    
    extent = [0, nx * dx, 0, nz * dz]
    
    im = ax.imshow(
        grids[0].T,
        origin="lower",
        cmap="viridis",
        vmin=vmin,
        vmax=vmax,
        extent=extent,
        aspect='auto'
    )
    cbar = plt.colorbar(im, ax=ax)
    cbar.set_label("Reflectivity (dBZ)")

    ax.set_xlabel("X (km from origin)")
    ax.set_ylabel("Z (km from origin)")
    title = ax.set_title(f"Step: {indices[0]}")

    plt.tight_layout()

    # ---- Animation update ----
    def update(frame):
        im.set_data(grids[frame].T)
        title.set_text(f"Step: {indices[frame]}")
        return im, title

    anim = FuncAnimation(
        fig,
        update,
        frames=len(grids),
        interval=300,
        blit=False
    )

    # ---- Save video ----
    os.makedirs("videos", exist_ok=True)
    output_video = "videos/cartesian_grid_animation.mp4"

    writer = FFMpegWriter(fps=4, bitrate=1800)
    anim.save(output_video, writer=writer)

    plt.close()

