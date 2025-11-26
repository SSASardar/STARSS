import re
import matplotlib.pyplot as plt
import numpy as np

def plot_fourier_spectrum(values, title="Fourier Spectrum of grid.data"):
    """
    Compute the Fourier Transform of the 1D grid_values array
    and plot its magnitude spectrum.
    """
    nonzero_vals = [v for v in values if v != 0]
    if not nonzero_vals:
        raise ValueError("All grid.data values are zero — nothing to plot.")



    # Convert to numpy array
    arr = np.array(nonzero_vals, dtype=float)
    #arr = np.array(values, dtype=float)
    # Remove NaN or inf if present
    arr = arr[np.isfinite(arr)]

    # Compute FFT
    fft_vals = np.fft.fft(arr)
    fft_freqs = np.fft.fftfreq(len(arr))

    # Use only the positive frequencies
    pos_mask = fft_freqs >= 0
    freqs = fft_freqs[pos_mask]
    magnitude = np.abs(fft_vals[pos_mask])

    # Plot
    plt.figure(figsize=(12, 6))
    plt.plot(freqs, magnitude)
    plt.title(title)
    plt.xlabel("Normalised Frequency")
    plt.ylabel("Magnitude")
    plt.grid(True)
    plt.tight_layout()
    plt.show()


def plot_radar_polar(path, n=2):
    """
    Plot the radar scan n as a polar heatmap (PPI view).
    """
    scan_blocks = get_radar_scan_blocks(path)
    
    if n < 0 or n >= len(scan_blocks):
        raise IndexError(f"Requested scan #{n}, but only {len(scan_blocks)} blocks exist.")
    
    scan_text = scan_blocks[n]
    
    # Extract grid.data
    match_data = re.search(r"grid\.data=([0-9eE\.\s\-\+]+)", scan_text)
    if not match_data:
        raise ValueError(f"grid.data block not found in scan #{n}.")
    values = [float(v) for v in match_data.group(1).strip().split()]
    
    # Extract number of ranges and angles
    match_ranges = re.search(r"box\.num_ranges=(\d+)", scan_text)
    match_angles = re.search(r"box\.num_angles=(\d+)", scan_text)
    if not match_ranges or not match_angles:
        raise ValueError(f"Could not find box.num_ranges or box.num_angles in scan #{n}.")
    
    num_ranges = int(match_ranges.group(1))
    num_angles = int(match_angles.group(1))
    
    # Extract min/max range and min/max angle
    match_min_range = re.search(r"box\.min_range_gate=([\d\.]+)", scan_text)
    match_max_range = re.search(r"box\.max_range_gate=([\d\.]+)", scan_text)
    match_min_angle = re.search(r"box\.min_angle=([\d\.]+)", scan_text)
    match_max_angle = re.search(r"box\.max_angle=([\d\.]+)", scan_text)
    
    if not (match_min_range and match_max_range and match_min_angle and match_max_angle):
        raise ValueError(f"Could not find min/max range or angle in scan #{n}.")
    
    min_range = float(match_min_range.group(1))
    max_range = float(match_max_range.group(1))
    min_angle = float(match_min_angle.group(1))
    max_angle = float(match_max_angle.group(1))
    
    # Reshape data
    grid_2d = np.array(values).reshape((num_ranges, num_angles))
    
    # Convert angles to radians for polar plotting
    theta = np.linspace(np.deg2rad(min_angle), np.deg2rad(max_angle), num_angles)
    r = np.linspace(min_range, max_range, num_ranges)
    
    # Create 2D grids for pcolormesh
    Theta, R = np.meshgrid(theta, r)
    
    # Plot polar heatmap
    fig, ax = plt.subplots(subplot_kw={'projection': 'polar'}, figsize=(8,8))
    c = ax.pcolormesh(Theta, R, grid_2d, cmap='viridis', shading='auto')
    fig.colorbar(c, ax=ax, label='Radar Intensity')
    ax.set_title(f"Radar PPI Heatmap (Scan #{n})")
    plt.show()



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

def plot_frequency(values):
    plt.figure(figsize=(10,5))
    plt.hist(values, bins=500)
    plt.title("Frequency Plot of grid.data (first radar scan)")
    plt.xlabel("Value")
    plt.ylabel("Frequency")
    plt.grid(True)
    plt.show()

def plot_frequency_shift_axis(values):
    # Find the smallest non-zero value
    nonzero_vals = [v for v in values if v != 0]
    if not nonzero_vals:
        raise ValueError("All grid.data values are zero — nothing to plot.")

    xmin = min(nonzero_vals)

    plt.figure(figsize=(10,5))
    plt.hist(values, bins=50)
    plt.title("Frequency Plot of grid.data (axis shifted to exclude zero)")
    plt.xlabel("Value")
    plt.ylabel("Frequency")
    plt.grid(True)

    # Shift axis so it starts at the smallest non-zero entry
    plt.xlim(xmin, max(values))

    plt.show()

def plot_frequency_nonzero(values):
    # Filter out zeros
    nonzero = [v for v in values if v >10]

    if not nonzero:
        raise ValueError("All grid.data values are zero — nothing to plot.")

    plt.figure(figsize=(10,5))
    plt.hist(nonzero, bins=50)
    plt.title("Frequency Plot of grid.data (non-zero values only)")
    plt.xlabel("Value")
    plt.ylabel("Frequency")
    plt.grid(True)

    # Set x-limits exactly around the min/max of non-zero values
    plt.xlim(min(nonzero), max(nonzero))

    plt.show()


if __name__ == "__main__":
    path = "outputs/C_RALA/radar_scan_0039.txt"
    #grid_values = extract_first_grid_data(path)
    grid_values = extract_grid_data_from_scan(path, n=2)
    #plot_frequency(grid_values)
    plot_radar_polar(path, n=2)
    plot_frequency_nonzero(grid_values)
    plot_fourier_spectrum(grid_values)
