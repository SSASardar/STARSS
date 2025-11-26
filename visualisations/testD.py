import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation, FFMpegWriter
from scipy.interpolate import interp1d
import glob
import os


# ---------------------------------------------------
# Load VPR file
# ---------------------------------------------------
def load_VPR(filename):
    refl, height = [], []
    with open(filename, "r") as f:
        for line in f:
            if line.startswith("#") or not line.strip():
                continue
            parts = line.split()
            if len(parts) >= 3:
                refl.append(float(parts[1]))
                height.append(float(parts[2]))
    return np.array(refl), np.array(height)


# ---------------------------------------------------
# Load convective VPR files
# ---------------------------------------------------
vpr_files = sorted(glob.glob("outputs/VPR_conv_*.txt"))
num_frames = len(vpr_files)

if num_frames == 0:
    raise RuntimeError("No VPR_conv files found in outputs/VPR_conv_*.txt")


# ---------------------------------------------------
# Load stratiform VPR (single file)
# ---------------------------------------------------
strat_file = "outputs/VPR_strat_0000.txt"
refl_s, h_s = load_VPR(strat_file)

# Interpolate stratiform curve if valid
if len(h_s) > 1:
    f_s = interp1d(h_s, refl_s, kind="linear", fill_value="extrapolate")
    h_smooth = np.linspace(min(h_s), max(h_s), 200)
    refl_smooth = f_s(h_smooth)
else:
    h_smooth, refl_smooth = h_s, refl_s


# ---------------------------------------------------
# Setup figure
# ---------------------------------------------------
fig, ax = plt.subplots(figsize=(6, 8))
ax.set_xlim(0, 60)
ax.set_ylim(0, 12000)
ax.set_xlabel("Reflectivity (dBZ)")
ax.set_ylabel("Height (m)")
ax.set_title("Vertical Profile (VPR)")

# --- static stratiform VPR ---
strat_line, = ax.plot(refl_smooth, h_smooth, 'g-', label="Stratiform VPR")

# --- animated convective VPR ---
vpr_line, = ax.plot([], [], 'r-', label="Convective VPR")
vpr_scatter = ax.scatter([], [], color='red', s=20)

ax.legend()


# ---------------------------------------------------
# Update function
# ---------------------------------------------------
def update(frame):
    refl, height = load_VPR(vpr_files[frame])

    # Smooth convective profile
    if len(height) > 1:
        f = interp1d(height, refl, kind="linear", fill_value="extrapolate")
        h_new = np.linspace(min(height), max(height), 200)
        refl_new = f(h_new)
        vpr_line.set_data(refl_new, h_new)
    else:
        vpr_line.set_data([], [])

    # Update scatter points
    vpr_scatter.set_offsets(np.c_[refl, height])

    # Update time label (assume 5-minute spacing)
    minutes = frame * 5
    ax.set_title(f"Vertical Profile (VPR) – {minutes} min")

    return [vpr_line, vpr_scatter]


# ---------------------------------------------------
# Animate and save
# ---------------------------------------------------
os.makedirs("outputs", exist_ok=True)
ani = FuncAnimation(fig, update, frames=num_frames, blit=False)

writer = FFMpegWriter(fps=5, bitrate=1800)
ani.save("outputs/VPR_conv_with_strat_animation.mp4", writer=writer)

print("Saved animation to outputs/VPR_conv_with_strat_animation.mp4")

