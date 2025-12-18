import numpy as np
import matplotlib.pyplot as plt

filename = "outputs/radar_scan_0039.txt"

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
            # stop after the first scan
            break

        if inside_scan:
            if line.startswith("box.num_angles="):
                n_angles = int(line.split("=")[1])
            if line.startswith("box.num_ranges="):
                n_ranges = int(line.split("=")[1])

            if line.startswith("grid.data="):
                # everything after '=' is the start of data
                data_str = line.split("=", 1)[1]
                # continue reading until we have all values
                values = data_str.split()
                while len(values) < n_angles * n_ranges:
                    values.extend(next(f).strip().split())
                grid_data = np.array(values, dtype=float)[: n_angles * n_ranges]

# reshape into (angles × ranges)
#grid = grid_data.reshape((n_ranges, n_angles), order = "F")
grid = grid_data.reshape((n_ranges,n_angles), order = "C")
#grid = np.fliplr(np.flipud(grid))
grid = np.transpose(grid)

# plot
plt.figure(figsize=(10, 6))
plt.imshow(grid, aspect='auto', origin='lower', cmap='turbo')
plt.colorbar(label="Reflectivity dBZ")
plt.xlabel("")
plt.ylabel("")
plt.title("")
plt.show()

