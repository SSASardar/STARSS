import numpy as np
import matplotlib.pyplot as plt
import glob
import os

def load_display_grid(filename):
    """Load display grid from file (skips comment lines starting with #)."""
    values = []
    with open(filename, "r") as f:
        for line in f:
            if line.startswith("#") or not line.strip():
                continue
            row = []
            for token in line.split():
                if token.lower() == "nan":
                    row.append(np.nan)
                else:
                    row.append(float(token))
            values.append(row)
    return np.array(values)

def plot_display_grid(infile, out_ext="png"):
    """Plot display grid and save to plots/ directory with same basename."""
    grid = load_display_grid(infile)

    # Make sure plots directory exists
    os.makedirs("plots", exist_ok=True)

    # Build output filename
    base = os.path.basename(infile)              # e.g. "disp_grid1.txt"
    name, _ = os.path.splitext(base)             # -> "disp_grid1"
    outfile = os.path.join("plots", f"{name}.{out_ext}")

    # Plot heatmap
    plt.figure(figsize=(6, 5))
    plt.imshow(grid.T, origin="lower", cmap="turbo", interpolation="nearest")
    plt.colorbar(label="Reflectivity (dBZ)")
    plt.title(name)
    plt.xlabel("X")
    plt.ylabel("Y")
    plt.tight_layout()

    plt.savefig(outfile, dpi=150)
    plt.close()
    print(f"Saved plot: {outfile}")

if __name__ == "__main__":
    # Process all files matching pattern
    for infile in glob.glob("outputs/zprevious/X-bandstuff/disp_grid*.txt"):
        plot_display_grid(infile, out_ext="png")

