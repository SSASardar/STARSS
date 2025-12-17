import numpy as np
import matplotlib.pyplot as plt

# Path to your file
filename = "outputs/radar_scans_0039.txt"

# Load the file
with open(filename, "r") as f:
    lines = f.readlines()

# Extract box info
num_ranges = None
num_angles = None
min_range_gate = None
range_res = None
min_angle = None
angular_res = None

for line in lines:
    if line.startswith("box.num_ranges"):
        num_ranges = int(line.strip().split("=")[1])
    elif line.startswith("box.num_angles"):
        num_angles = int(line.strip().split("=")[1])
    elif line.startswith("box.min_range_gate"):
        min_range_gate = float(line.strip().split("=")[1])
    elif line.startswith("box.range_resolution"):
        range_res = float(line.strip().split("=")[1])
    elif line.startswith("box.min_angle"):
        min_angle = float(line.strip().split("=")[1])
    elif line.startswith("box.angular_resolution"):
        angular_res = float(line.strip().split("=")[1])
    elif line.startswith("grid.data"):
        data_str = line.strip().split("=")[1]
        grid_data = np.array([float(x) for x in data_str.split()])

# Reshape the flattened grid into 2D array (num_ranges x num_angles)
grid_2d = grid_data.reshape((num_ranges, num_angles))

# Create range and elevation arrays
ranges = min_range_gate + np.arange(num_ranges) * range_res
angles = min_angle + np.arange(num_angles) * angular_res

# Plot the heatmap
plt.figure(figsize=(10, 6))
plt.imshow(grid_2d.T,  # Transpose to have elevation on y-axis
           origin='lower',
           extent=[ranges[0], ranges[-1], angles[0], angles[-1]],
           aspect='auto',
           cmap='jet')
plt.colorbar(label='Reflectivity (dBZ)')
plt.xlabel('Range (m)')
plt.ylabel('Elevation (deg)')
plt.title('RHI Radar Scan Heatmap')
plt.show()

