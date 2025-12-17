import re
import matplotlib.pyplot as plt
import numpy as np

def get_radar_scan_blocks(path):
    """Return all scan blocks split by the delimiter."""
    with open(path, "r") as f:
        text = f.read()

    blocks = re.split(r"=== BEGIN RADAR_SCAN ===", text)
    blocks = [b.strip() for b in blocks if b.strip()]
    return blocks


def extract_grid_data_from_scan_block(scan_text):
    """Extract grid.data from a single scan block."""
    match = re.search(r"grid\.data=([0-9eE\.\s\-\+]+)", scan_text)
    if not match:
        return None
    values = match.group(1).strip().split()
    return [float(v) for v in values]


def extract_all_scans(path):
    """Return a list of lists: grid.data values for every scan in the file."""
    blocks = get_radar_scan_blocks(path)
    all_scans = []

    for b in blocks:
        vals = extract_grid_data_from_scan_block(b)
        if vals is not None:
            all_scans.append(vals)

    return all_scans


def plot_all_scans_overlaid_nonzero_with_stats(all_scan_values):
    plt.figure(figsize=(14, 7))

    # soft colormap with many distinct colors
    cmap = plt.cm.tab20
    num_colors = cmap.N

    for i, scan_vals in enumerate(all_scan_values):
        nonzero = np.array([v for v in scan_vals if v != 0])
        if len(nonzero) == 0:
            continue

        color = cmap(i % num_colors)

        # Plot histogram (soft opacity)
        plt.hist(
            nonzero,
            bins=80,
            alpha=0.18,
            color=color,
            label=f"Scan {i}",
        )

        # Compute stats
        mean = np.mean(nonzero)
        stdev = np.std(nonzero, ddof=1)  # sample stdev
        
        # Plot mean line
        #plt.axvline(mean, color=color, linewidth=2)

        # Plot ± stdev
        #plt.axvline(mean - stdev, color=color, linestyle="--", linewidth=1)
        #plt.axvline(mean + stdev, color=color, linestyle="--", linewidth=1)

        # Optional: Label each mean
        #plt.text(mean, plt.ylim()[1]*0.95, f"{i}", color=color, fontsize=8,
        #         ha='center', va='top')

    plt.title("Overlaid Histograms of All Scans (Non-zero Values)\nWith Mean and ±1σ Markers")
    plt.xlabel("Value")
    plt.ylabel("Frequency")
    plt.grid(True)
    plt.legend(fontsize=8, ncol=2)
    plt.tight_layout()
    plt.show()


if __name__ == "__main__":
    path = "outputs/zprevious/X-band stuff/radar_scan_0039.txt"

    all_scan_values = extract_all_scans(path)

    plot_all_scans_overlaid_nonzero_with_stats(all_scan_values)

