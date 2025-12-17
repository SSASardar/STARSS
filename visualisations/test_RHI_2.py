import numpy as np
import matplotlib.pyplot as plt

filename = "outputs/radar_scan_0039.txt"

grid_data = []
num_ranges = None
num_angles = None

with open(filename) as f:
    for line in f:
        line = line.strip()

        if line.startswith("box.num_ranges"):
            num_ranges = int(line.split("=")[1])
        elif line.startswith("box.num_angles"):
            num_angles = int(line.split("=")[1])
        elif line.startswith("grid.data="):
            # everything after '=' is the numbers
            data_str = line.split("=",1)[1]
            grid_data = [float(x) for x in data_str.split()]
            break

# Convert to numpy
grid_data = np.array(grid_data)

# ✔ Correct reshape: angle is fastest index
grid = grid_data.reshape((num_ranges, num_angles))

#plt.imshow(grid, origin="lower", aspect="auto", cmap="turbo")
#plt.xlabel("Angle index")
#plt.ylabel("Range index")
#plt.colorbar(label="Reflectivity (dBZ)")
#plt.show()

plt.imshow(grid, origin="lower", aspect="auto", cmap="turbo")
plt.xlabel("Range index")
plt.ylabel("Angle index")
plt.colorbar(label="Reflectivity (dBZ)")
plt.show()
