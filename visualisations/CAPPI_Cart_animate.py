import os
import glob
import re
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation, FFMpegWriter

# ------------------------------------------------------------
# File handling
# ------------------------------------------------------------

def list_output_files(folder="outputs/zprevious/X-bandstuff/"):
    pattern = os.path.join(folder, "disp_g*.txt")
    return glob.glob(pattern)


def extract_index(filename):
    """
    Extract trailing integer index from filename.
    Example: disp_g123.txt -> 123
    """
    basename = os.path.basename(filename)
    match = re.search(r"(\d+)(?=\.txt$)", basename)
    if not match:
        raise ValueError(f"No numeric index in filename: {basename}")
    return int(match.group(1))


def load_grid_from_file(filename):
    """
    Loads grid while:
    - Skipping header lines starting with '#'
    - Parsing expected grid size
    - Handling 'NaN'
    """
    data = []
    expected_shape = None

    with open(filename, "r") as f:
        for line in f:
            line = line.strip()

            # Parse grid size from header
            if line.startswith("# Grid size:"):
                parts = line.split(":")[1].strip().split("x")
                expected_shape = (
                    int(parts[0].strip()),
                    int(parts[1].strip())
                )

            # Skip header / blank lines
            if not line or line.startswith("#"):
                continue

            row = [
                float(x) if x.lower() != "nan" else np.nan
                for x in line.split()
            ]
            data.append(row)

    grid = np.array(data, dtype=float)

    # Validate shape if header was present
    if expected_shape and grid.shape != expected_shape:
        raise ValueError(
            f"{filename} shape mismatch: "
            f"{grid.shape} vs {expected_shape}"
        )

    return grid


# ------------------------------------------------------------
# Bottom-right anchoring
# ------------------------------------------------------------

def pad_bottom_right(grid, canvas_shape):
    """
    Places grid on canvas so bottom-right corner is fixed.
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
        raise RuntimeError("No disp_g*.txt files found in outputs/")

    # ---- Sort numerically ----
    file_index_pairs = [(extract_index(f), f) for f in files]
    file_index_pairs.sort(key=lambda x: x[0])

    # ---- Load grids & determine max canvas size ----
    raw_grids = []
    indices = []
    max_rows = 0
    max_cols = 0

    for idx, f in file_index_pairs:
        print(f"Loading {f}")
        g = load_grid_from_file(f)
        raw_grids.append(g)
        indices.append(idx)
        max_rows = max(max_rows, g.shape[0])
        max_cols = max(max_cols, g.shape[1])

    canvas_shape = (max_rows, max_cols)
    print(f"Canvas size: {canvas_shape}")

    # ---- Anchor grids to bottom-right ----
    grids = np.array([
        pad_bottom_right(g, canvas_shape)
        for g in raw_grids
    ])

    # ---- Fixed reflectivity scale ----
    vmin = 0
    vmax = 90

    # ---- Figure setup ----
    fig, ax = plt.subplots(figsize=(8, 5))

    # Physical grid spacing (meters)
    dx = 0.025
    dz = 0.025

    nx = canvas_shape[1]
    nz = canvas_shape[0]

    extent = [0, nx * dx, 0, nz * dz]

    im = ax.imshow(
        grids[0].T,
        origin="lower",
        cmap="viridis",
        vmin=vmin,
        vmax=vmax,
        extent=extent,
        aspect="auto"
    )

    cbar = plt.colorbar(im, ax=ax)
    cbar.set_label("Reflectivity (dBZ)")

    ax.set_xlabel("size X (km)")
    ax.set_ylabel("size Y (km)")
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
    output_video = "videos/disp_grid_animation.mp4"

    writer = FFMpegWriter(fps=4, bitrate=1800)
    anim.save(output_video, writer=writer)

    print(f"Saved animation to {output_video}")
    plt.close()
