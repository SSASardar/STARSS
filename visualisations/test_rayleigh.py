import re
import matplotlib.pyplot as plt
import math

def get_radar_scan_blocks(path):
    """Return all scan blocks split by the delimiter."""
    with open(path, "r") as f:
        text = f.read()

    # Split on the exact delimiter
    blocks = re.split(r"=== BEGIN RADAR_SCAN ===", text)

    # Remove empty whitespace-only entries
    blocks = [b.strip() for b in blocks if b.strip()]

    return blocks

def extract_grid_data_from_scan(path, n=0):
    """
    Extract grid.data values from the nth radar scan block.
    n=0 → first scan
    n=1 → second scan, etc.
    """

    scan_blocks = get_radar_scan_blocks(path)

    if n < 0 or n >= len(scan_blocks):
        raise IndexError(f"Requested scan #{n}, but only {len(scan_blocks)} blocks exist.")

    scan_text = scan_blocks[n]

    # Extract the grid.data block (may span multiple lines)
    match = re.search(r"grid\.data=([0-9eE\.\s\-\+]+)", scan_text)
    if not match:
        raise ValueError(f"grid.data block not found in scan #{n}.")

    # Convert whitespace-separated numbers to floats
    values = match.group(1).strip().split()
    return [float(v) for v in values]


def extract_first_grid_data(path):
    with open(path, "r") as f:
        text = f.read()

    # Extract the first radar scan block
    scan_blocks = re.split(r"=== BEGIN RADAR_SCAN ===", text)
    if len(scan_blocks) < 2:
        raise ValueError("No radar scan blocks found.")

    first_scan = scan_blocks[1]

    # Extract the grid.data= line (values may span multiple lines)
    match = re.search(r"grid\.data=([0-9eE\.\s\-\+]+)", first_scan)
    if not match:
        raise ValueError("grid.data block not found in first scan.")

    # Split values by whitespace
    values = match.group(1).strip().split()
    return [float(v) for v in values]


def compute_stats_nonzero(values):
    nonzero = [v for v in values if v != 0]

    if not nonzero:
        raise ValueError("All grid.data values are zero — nothing to compute.")

    n = len(nonzero)
    mean = sum(nonzero) / n

    # Sample variance: divide by (n-1)
    var = sum((v - mean) ** 2 for v in nonzero) / (n - 1)

    stdev = math.sqrt(var)
    ratio = stdev / mean if mean != 0 else float('inf')

    return mean, var, stdev, ratio


if __name__ == "__main__":
    path = "outputs/radar_scan_0005.txt"
    #grid_values = extract_first_grid_data(path)
    grid_values = extract_grid_data_from_scan(path, n=1)

    mean, var, stdev, ratio = compute_stats_nonzero(grid_values)

    print("Nonzero sample mean:", mean)
    print("Nonzero sample variance:", var)
    print("Nonzero sample stdev:", stdev)
    print("stdev / mean:", ratio)

