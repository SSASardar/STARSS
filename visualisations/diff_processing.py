import numpy as np
import matplotlib.pyplot as plt

# Load the two files (skip header row)
max_data = np.loadtxt("outputs/stats_RALA_X.txt", skiprows=1)
rala_data = np.loadtxt("outputs/stats_RALA_C.txt", skiprows=1)

# Columns (based on your format):
# 0=Scan, 1=MSE, 2=MAE, 3=Bias,
# 4=Total_meas, 5=Total_true_unmasked,
# 6=Total_meas_mm2, 7=Total_true_mm2_unmasked

# Extract relevant columns
scan_id = max_data[:, 0]
scans_max = max_data[:, 0]
meas_max = max_data[:, 6]
time = scan_id * 5.0  # minutes


scans_rala = rala_data[:, 0]
meas_rala = rala_data[:, 6]

true_mm2 = max_data[:, 7]  # same across rows

# Plot
plt.figure(figsize=(10, 6))
plt.plot(time, meas_max, label="RALA X-band", marker="o", color="purple", linestyle="dotted")
plt.plot(time, meas_rala, label="RALA C-band", marker="o", color="blue", linestyle="dashed")
plt.plot(time, true_mm2, label="True rate", color="orange", linestyle="solid")


# Compute absolute differences
diff_max = np.abs(meas_max - true_mm2)
diff_rala = np.abs(meas_rala - true_mm2)

# Sum of differences (total error)
total_diff_max = np.sum(diff_max)
total_diff_rala = np.sum(diff_rala)

# Relative improvement of RALA vs Max
relative_improvement = (total_diff_max - total_diff_rala) / total_diff_max * 100

# Print results
print(f"Total error (RALA X-band):   {total_diff_max:.4f}")
print(f"Total error (RALA C-band):  {total_diff_rala:.4f}")
print(f"Relative improvement of X-band over C-band: {relative_improvement:.2f}%")


plt.xlabel("Time (mins)")
plt.ylabel("Rainfall rate [mm per sec per m²]")
plt.title("Effects of radar on measured rainfall rate")
plt.legend()
plt.grid(True, linestyle="--", alpha=0.6)
plt.tight_layout()
plt.show()
