import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation, FFMpegWriter
import glob
import os
import re

# -----------------------
# Helper functions
# -----------------------
def load_grid(filename):
    values = []
    with open(filename, "r") as f:
        for line in f:
            if line.startswith("#") or not line.strip():
                continue
            row = [float(tok) if tok.lower() != "nan" else np.nan for tok in line.split()]
            values.append(row)
    return np.array(values)

def pad_grid(grid, target_shape):
    padded = np.full(target_shape, np.nan)
    rows, cols = grid.shape
    padded[:rows, :cols] = grid
    return padded

def downsample(grid, factor=2):
    return grid[::factor, ::factor]

# -----------------------
# Load grid files
# -----------------------
# Regular radar grids
disp_files = sorted(glob.glob("outputs/disp_g_*.txt"))
true_files = sorted(glob.glob("outputs/true_g_*.txt"))

# Adaptive radar grids
ad_disp_files = sorted(glob.glob("outputs/ad_disp_g_*.txt"))

print(f"Found {len(disp_files)} regular radar files")
print(f"Found {len(ad_disp_files)} adaptive radar files")
print(f"Found {len(true_files)} true reflectivity files")

disp_grids_raw = [load_grid(f) for f in disp_files]
true_grids_raw = [load_grid(f) for f in true_files]
ad_disp_grids_raw = [load_grid(f) for f in ad_disp_files]

# Determine max dimensions for padding
max_rows = max(max(g.shape[0] for g in disp_grids_raw),
               max(g.shape[0] for g in true_grids_raw),
               max(g.shape[0] for g in ad_disp_grids_raw))
max_cols = max(max(g.shape[1] for g in disp_grids_raw),
               max(g.shape[1] for g in true_grids_raw),
               max(g.shape[1] for g in ad_disp_grids_raw))

print(f"Grid dimensions: {max_rows} x {max_cols}")

# Pad and downsample all grids
disp_grids = [downsample(pad_grid(g, (max_rows, max_cols)), factor=2) for g in disp_grids_raw]
true_grids = [downsample(pad_grid(g, (max_rows, max_cols)), factor=2) for g in true_grids_raw]
ad_disp_grids = [downsample(pad_grid(g, (max_rows, max_cols)), factor=2) for g in ad_disp_grids_raw]

num_frames = len(disp_grids)

# Calculate consistent color limits
all_grids = disp_grids + true_grids + ad_disp_grids
vmin = min(np.nanmin(g) for g in all_grids)
vmax = max(np.nanmax(g) for g in all_grids)
print(f"Reflectivity range: {vmin:.2f} to {vmax:.2f} dBZ")

# -----------------------
# Load stats
# -----------------------
# Regular stats
stats = np.loadtxt("outputs/stats.txt", skiprows=1)
scan_id = stats[:, 0]
MSE = stats[:, 1]
MAE = stats[:, 2]
Bias = stats[:, 3]
total_measured_mm2 = stats[:, 6]
total_true_mm2 = stats[:, 7]
time = scan_id * 5.0  # minutes

# Adaptive stats
ad_stats = np.loadtxt("outputs/ad_stats.txt", skiprows=1)
ad_scan_id = ad_stats[:, 0]
ad_total_measured_mm2 = ad_stats[:, 6]
ad_time = ad_scan_id * 5.0  # minutes

print(f"Regular stats: {len(total_measured_mm2)} measurements")
print(f"Adaptive stats: {len(ad_total_measured_mm2)} measurements")

# -----------------------
# Setup figure
# -----------------------
fig = plt.figure(figsize=(18, 10))
gs = fig.add_gridspec(2, 3, height_ratios=[2, 1], hspace=0.3, wspace=0.3)

# Top row: three reflectivity plots
ax_ad = fig.add_subplot(gs[0, 0])
ax_disp = fig.add_subplot(gs[0, 1])
ax_true = fig.add_subplot(gs[0, 2])

# Bottom row: Stats plot spanning all three columns
ax_stats = fig.add_subplot(gs[1, :])

# Initialize the reflectivity plots
cmap = 'viridis'
im_ad = ax_ad.imshow(ad_disp_grids[0].T, cmap=cmap, origin='lower', 
                     vmin=vmin, vmax=vmax)
im_disp = ax_disp.imshow(disp_grids[0].T, cmap=cmap, origin='lower', 
                         vmin=vmin, vmax=vmax)
im_true = ax_true.imshow(true_grids[0].T, cmap=cmap, origin='lower', 
                         vmin=vmin, vmax=vmax)

# Set titles
ax_ad.set_title("What the adaptive radar sees", fontsize=12, fontweight='bold')
ax_disp.set_title("What the radar sees", fontsize=12, fontweight='bold')
ax_true.set_title("Refl. at lowest alt.", fontsize=12, fontweight='bold')

# Add labels
for ax in [ax_ad, ax_disp, ax_true]:
    ax.set_xlabel("X coordinate")
    ax.set_ylabel("Y coordinate")

# Add colorbar for top row
cbar_ax = fig.add_axes([0.92, 0.55, 0.02, 0.35])
cbar = fig.colorbar(im_disp, cax=cbar_ax)
cbar.set_label("Reflectivity (dBZ)", rotation=270, labelpad=15)

# Initialize stats plot
line_regular, = ax_stats.plot([], [], marker='o', color='purple', 
                               linewidth=2, markersize=6, label='Regular radar')
line_adaptive, = ax_stats.plot([], [], marker='s', color='red', 
                                linewidth=2, markersize=6, label='Adaptive radar')
line_true, = ax_stats.plot([], [], marker='^', color='orange', 
                           linewidth=2, markersize=6, label='True')

# Time indicator line
time_line = ax_stats.axvline(time[0], color='black', linestyle='--', alpha=0.7)

# Setup stats plot
ax_stats.set_title("True vs Measured Rainfall Rate Over Time", fontsize=12, fontweight='bold')
ax_stats.set_xlabel("Time (minutes)")
ax_stats.set_ylabel("Rainfall rate [mm per sec per m²]")
ax_stats.legend(loc='best', fontsize=10)
ax_stats.grid(True, alpha=0.3)
ax_stats.set_xlim(0, max(time.max(), ad_time.max()))
ax_stats.set_ylim(0, max(total_measured_mm2.max(), ad_total_measured_mm2.max(), total_true_mm2.max()) * 1.1)

# Text box for current statistics
stats_text = ax_stats.text(0.02, 0.98, '', transform=ax_stats.transAxes,
                          fontsize=9, verticalalignment='top',
                          bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))

# Add timestamp text
timestamp_text = fig.suptitle("", fontsize=14, fontweight='bold')

# Pre-plot the full time series
ax_stats.plot(time, total_measured_mm2, color='purple', alpha=0.3, linewidth=1)
ax_stats.plot(ad_time, ad_total_measured_mm2, color='red', alpha=0.3, linewidth=1)
ax_stats.plot(time, total_true_mm2, color='orange', alpha=0.3, linewidth=1)

# -----------------------
# Update function
# -----------------------
def update(frame):
    """Update the animation for each frame"""
    timestamp_min = frame * 5
    
    # Update reflectivity plots
    im_ad.set_data(ad_disp_grids[frame].T)
    im_disp.set_data(disp_grids[frame].T)
    im_true.set_data(true_grids[frame].T)
    
    # Update titles with timestamp
    ax_ad.set_title(f"What the adaptive radar sees\n{timestamp_min} min", fontsize=12, fontweight='bold')
    ax_disp.set_title(f"What the radar sees\n{timestamp_min} min", fontsize=12, fontweight='bold')
    ax_true.set_title(f"Refl. at lowest alt.\n{timestamp_min} min", fontsize=12, fontweight='bold')
    
    # Update the time series lines to show up to current frame
    current_time = timestamp_min
    
    # Regular radar data (up to current frame)
    mask_regular = time <= current_time
    line_regular.set_data(time[mask_regular], total_measured_mm2[mask_regular])
    
    # Adaptive radar data (up to current frame)
    mask_adaptive = ad_time <= current_time
    line_adaptive.set_data(ad_time[mask_adaptive], ad_total_measured_mm2[mask_adaptive])
    
    # True data (up to current frame)
    mask_true = time <= current_time
    line_true.set_data(time[mask_true], total_true_mm2[mask_true])
    
    # Update time indicator line
    time_line.set_xdata([current_time])
    
    # Update statistics text box
    if frame < len(total_measured_mm2):
        current_regular = total_measured_mm2[frame]
        current_adaptive = ad_total_measured_mm2[frame] if frame < len(ad_total_measured_mm2) else np.nan
        current_true = total_true_mm2[frame]
        
        if not np.isnan(current_adaptive):
            regular_error = abs(current_regular - current_true)
            adaptive_error = abs(current_adaptive - current_true)
            improvement = (regular_error - adaptive_error) / regular_error * 100 if regular_error > 0 else 0
            
            stats_text_str = f"Time: {timestamp_min} min\n"
            stats_text_str += f"Regular radar: {current_regular:.2f}\n"
            stats_text_str += f"Adaptive radar: {current_adaptive:.2f}\n"
            stats_text_str += f"True: {current_true:.2f}\n"
            stats_text_str += f"Regular error: {regular_error:.2f}\n"
            stats_text_str += f"Adaptive error: {adaptive_error:.2f}\n"
            stats_text_str += f"Improvement: {improvement:.1f}%"
            
            # Change text color based on improvement
            if improvement > 0:
                stats_text_str += " ✓"
            
            stats_text.set_text(stats_text_str)
    
    # Update main title
    timestamp_text.set_text(f"Radar Comparison - Time: {timestamp_min} minutes")
    
    return [im_ad, im_disp, im_true, line_regular, line_adaptive, line_true, 
            time_line, stats_text, timestamp_text]

# -----------------------
# Create animation
# -----------------------
print(f"Creating animation with {num_frames} frames...")

# Create animation
ani = FuncAnimation(fig, update, frames=num_frames, blit=False, interval=200, repeat=True)

# Save as video
os.makedirs("outputs", exist_ok=True)
writer = FFMpegWriter(fps=5, metadata=dict(artist='Radar Comparison'), bitrate=3000)
ani.save("outputs/radar_comparison_animation.mp4", writer=writer)
print("Saved animation to outputs/radar_comparison_animation.mp4")

# Optional: Also save as GIF
try:
    ani.save("outputs/radar_comparison_animation.gif", writer='pillow', fps=5)
    print("Saved GIF to outputs/radar_comparison_animation.gif")
except Exception as e:
    print(f"Could not save GIF: {e}")

print("\nAnimation created successfully!")
