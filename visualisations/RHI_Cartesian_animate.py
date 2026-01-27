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
    pattern = os.path.join(folder, "*cartesian_grid*.txt")
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
    vmin = np.nanmin(grids)
    vmax = np.nanmax(grids)

    # ---- Figure setup ----
    fig, ax = plt.subplots(figsize=(10, 10))

    im = ax.imshow(
        grids[0].T,
        origin="lower",
        cmap="viridis",
        vmin=vmin,
        vmax=vmax
    )

    cbar = plt.colorbar(im, ax=ax)
    cbar.set_label("Value")

    ax.set_xlabel("X index (resolution of 25m)")
    ax.set_ylabel("Z index (resolution of 25m)")
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

