import re
import numpy as np
import matplotlib.pyplot as plt


# ---------------------------------------------------------
# Extract metadata + first radar scan grid.data
# ---------------------------------------------------------
def extract_first_scan(path):
    with open(path, "r") as f:
        text = f.read()

    # Split into scan blocks
    scan_blocks = re.split(r"=== BEGIN RADAR_SCAN ===", text)
    if len(scan_blocks) < 2:
        raise ValueError("No radar scan blocks found.")

    first_scan = scan_blocks[1]

    # Extract number of angles
    angles_match = re.search(r"box\.num_angles\s*=\s*([0-9]+)", first_scan)
    if not angles_match:
        raise ValueError("Could not find box.num_angles in first scan.")
    num_angles = int(angles_match.group(1))

    # Extract number of ranges
    ranges_match = re.search(r"box\.num_ranges\s*=\s*([0-9]+)", first_scan)
    if not ranges_match:
        raise ValueError("Could not find box.num_ranges in first scan.")
    num_ranges = int(ranges_match.group(1))

    # Extract the grid.data block
    data_match = re.search(r"grid\.data=([0-9eE\.\s\-\+]+)", first_scan)
    if not data_match:
        raise ValueError("Could not find grid.data in first scan.")

    raw_values = data_match.group(1).strip().split()
    grid_values = [float(v) for v in raw_values]

    return grid_values, num_angles, num_ranges


# ---------------------------------------------------------
# Plot histogram AND heatmap side-by-side
# ---------------------------------------------------------
def plot_side_by_side(values, num_angles, num_ranges):
    # Prepare histogram axis shift
    nonzero = [v for v in values if v != 0]
    if not nonzero:
        raise ValueError("All grid.data values are zero — cannot plot histogram.")

    xmin = min(nonzero)

    # Reshape for heatmap
    expected_size = num_angles * num_ranges
    if len(values) != expected_size:
        raise ValueError(
            f"grid.data size mismatch: expected {expected_size}, got {len(values)}"
        )

    grid = np.array(values).reshape((num_angles, num_ranges))

    # Side-by-side layout
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))

    # Histogram
    ax1.hist(values, bins=50)
    ax1.set_title("Frequency Plot (zero excluded from axis)")
    ax1.set_xlabel("Value")
    ax1.set_ylabel("Frequency")
    ax1.grid(True)
    ax1.set_xlim(xmin, max(values))

    # Heatmap
    im = ax2.imshow(grid, aspect='auto', origin='lower')
    ax2.set_title("Heatmap of grid.data")
    ax2.set_xlabel("Range index")
    ax2.set_ylabel("Angle index")
    fig.colorbar(im, ax=ax2, label="Value")

    plt.tight_layout()
    plt.show()


# ---------------------------------------------------------
# Main
# ---------------------------------------------------------
if __name__ == "__main__":
    path = "outputs/radar_scan_0003.txt"

    print("Reading first radar scan and metadata...")
    grid_values, num_angles, num_ranges = extract_first_scan(path)

    print(f"Detected num_angles={num_angles}, num_ranges={num_ranges}")
    print("Plotting histogram + heatmap...")
    plot_side_by_side(grid_values, num_angles, num_ranges)

