import numpy as np
import matplotlib.pyplot as plt
import stylesheet  # centralised stylesheet
import os
import glob
import re
import sys

# ===========================
# FUNCTION TO FIND STATS FILE
# ===========================

def find_stats_file(folder_path, params):
    """
    Find the stats file matching the given parameters.
    
    Parameters:
    - folder_path: path to the folder containing stats files
    - params: dict with keys x1, x2, x3, x4, x5, x6, x7
    
    Returns:
    - path to the matching stats file, or None if not found
    """
    # Build the filename pattern
    filename_pattern = f"stats_x1_{params['x1']:03d}_x2_{params['x2']:03d}_x3_{params['x3']:03d}_x4_{params['x4']:02d}_x5_{params['x5']:02d}_x6_{params['x6']:03d}_x7_{params['x7']:03d}.txt"
    
    # Search for the file
    search_pattern = os.path.join(folder_path, filename_pattern)
    files = glob.glob(search_pattern)
    
    if files:
        return files[0]
    else:
        return None

# ===========================
# FUNCTION TO GET PARAMETER INPUT
# ===========================

def get_parameter_input():
    """
    Interactive function to get parameter values from the user.
    """
    print("\n" + "="*50)
    print("  SELECT PARAMETER COMBINATION")
    print("="*50)
    print("\nEnter parameter values (or press Enter to use default)\n")
    
    # Parameter definitions: (name, display, default, format, range)
    params = {
        'x1': {'display': 'Radius of raincell (km ×100)', 'default': 10, 'format': '03d', 'range': (0, 999)},
        'x2': {'display': 'Core ratio (×100)', 'default': 30, 'format': '03d', 'range': (0, 99)},
        'x3': {'display': 'Rain intensity (mm/hr)', 'default': 35, 'format': '03d', 'range': (0, 999)},
        'x4': {'display': 'Apparent motion (m/s ×10)', 'default': 9, 'format': '02d', 'range': (0, 99)},
        'x5': {'display': 'Cloud base height (km ×100)', 'default': 2, 'format': '02d', 'range': (0, 99)},
        'x6': {'display': 'Distance to C-band radar (km)', 'default': 30, 'format': '03d', 'range': (0, 999)},
        'x7': {'display': 'Storm duration (minutes)', 'default': 30, 'format': '03d', 'range': (1, 999)}
    }
    
    # Get user input for each parameter
    values = {}
    for key, param in params.items():
        while True:
            try:
                default_str = str(param['default'])
                user_input = input(f"  {param['display']} ({key}) [{default_str}]: ").strip()
                
                if user_input == '':
                    values[key] = param['default']
                    break
                else:
                    value = int(user_input)
                    if param['range'][0] <= value <= param['range'][1]:
                        values[key] = value
                        break
                    else:
                        print(f"    ⚠️ Value must be between {param['range'][0]} and {param['range'][1]}")
            except ValueError:
                print("    ⚠️ Please enter a valid integer")
    
    return values

# ===========================
# FUNCTION TO SHOW AVAILABLE PARAMETER VALUES
# ===========================

def show_available_parameters(folder_path):
    """
    Show the available parameter values in the folder.
    """
    files = glob.glob(os.path.join(folder_path, "stats_x1_*.txt"))
    
    if not files:
        print("❌ No stats files found in the folder!")
        return None
    
    # Extract parameter sets
    param_sets = {'x1': set(), 'x2': set(), 'x3': set(), 'x4': set(), 
                  'x5': set(), 'x6': set(), 'x7': set()}
    
    for file in files:
        filename = os.path.basename(file)
        # Extract parameters using regex
        pattern = r"stats_x1_(\d+)_x2_(\d+)_x3_(\d+)_x4_(\d+)_x5_(\d+)_x6_(\d+)_x7_(\d+)\.txt"
        match = re.search(pattern, filename)
        
        if match:
            param_sets['x1'].add(int(match.group(1)))
            param_sets['x2'].add(int(match.group(2)))
            param_sets['x3'].add(int(match.group(3)))
            param_sets['x4'].add(int(match.group(4)))
            param_sets['x5'].add(int(match.group(5)))
            param_sets['x6'].add(int(match.group(6)))
            param_sets['x7'].add(int(match.group(7)))
    
    # Display available values
    print("\n" + "-"*50)
    print("  AVAILABLE PARAMETER VALUES")
    print("-"*50)
    param_display = {
        'x1': 'Radius of raincell (km ×100)',
        'x2': 'Core ratio (×100)',
        'x3': 'Rain intensity (mm/hr)',
        'x4': 'Apparent motion (m/s ×10)',
        'x5': 'Cloud base height (km ×100)',
        'x6': 'Distance to C-band radar (km)',
        'x7': 'Storm duration (minutes)'
    }
    
    for key in sorted(param_sets.keys()):
        values = sorted(param_sets[key])
        print(f"  {key} ({param_display[key]}): {values}")
    print("-"*50)
    
    return param_sets

# ===========================
# FUNCTION TO PLOT STATS
# ===========================

def plot_stats(filepath, params):
    """
    Load and plot the stats file.
    """
    # Load data
    stats = np.loadtxt(filepath, skiprows=1)
    scan_id = stats[:, 0]
    total_measured_mm2 = stats[:, 6]
    total_true_mm2 = stats[:, 7]
    time = scan_id * 5.0  # minutes
    
    # Create figure
    fig, ax = plt.subplots(figsize=(12, 4))
    
    # Plot true values
    ax.plot(time, total_true_mm2, 
            color=stylesheet.COLORS['black'], 
            label='True',
            linewidth=1,
            markersize=3)
    
    # Plot measured values
    ax.plot(time, total_measured_mm2, 
            marker='^', 
            color=stylesheet.COLORS['black'], 
            label='Measured (C-band)',
            linewidth=1,
            markersize=3,
            linestyle='-.')
    
    # Set axes limits
    ax.set_xlim(left=0)
    ax.set_ylim(bottom=0)
    
    # ===========================
    # DYNAMIC REGION BOUNDARIES BASED ON x7
    # ===========================
    
    # Get x7 value (storm duration in minutes)
    x7 = params['x7']
    
    # Define time points
    t1 = 60          # UNINITIATED ends, GROWTH starts (fixed)
    t2 = 120         # GROWTH ends, MATURE starts (fixed)
    t4 = 230 - x7    # MATURE ends, DECAY starts (depends on x7)
    t5 = 230         # DECAY ends (fixed)
    
    # Ensure t4 is not less than t2 (mature phase must be at least 0 minutes)
    if t4 < t2:
        t4 = t2
    
    # Ensure t4 is not greater than t5
    if t4 > t5:
        t4 = t5
    
    # Add vertical lines
    ax.axvline(t1, color='black', linestyle='--', linewidth=0.8, alpha=0.7)
    ax.axvline(t2, color='black', linestyle='--', linewidth=0.8, alpha=0.7)
    ax.axvline(t4, color='black', linestyle='--', linewidth=0.8, alpha=0.7)
    ax.axvline(t5, color='black', linestyle='--', linewidth=0.8, alpha=0.7)
    
    # Shaded regions
    xmin, xmax = ax.get_xlim()
    ymin, ymax = ax.get_ylim()
    y_range = ymax - ymin
    
    # UNINITIATED region (0 to 60 min)
    ax.axvspan(0, t1, alpha=0.15, color=stylesheet.COLORS['strat'], label='_nolegend_')
    ax.text(0.05 * t1, ymax - 0.05 * y_range, 'UNINITIATED', 
            ha='left', va='top', fontsize=9, fontweight='bold', 
            color=stylesheet.COLORS['strat'], alpha=1)
    
    # GROWTH region (60 to 120 min)
    ax.axvspan(t1, t2, alpha=0.15, color=stylesheet.COLORS['growth'], label='_nolegend_')
    ax.text(t1 + 0.05 * (t2 - t1), ymax - 0.05 * y_range, 'GROWTH', 
            ha='left', va='top', fontsize=9, fontweight='bold', 
            color=stylesheet.COLORS['growth'], alpha=1)
    
    # MATURE region (120 to 230 - x7)
    ax.axvspan(t2, t4, alpha=0.15, color=stylesheet.COLORS['mature'], label='_nolegend_')
    if t4 - t2 > 10:  # Only show text if region is wide enough
        ax.text(t2 + 0.05 * (t4 - t2), ymax - 0.05 * y_range, 'MATURE', 
                ha='left', va='top', fontsize=9, fontweight='bold', 
                color=stylesheet.COLORS['mature'], alpha=1)
    else:
        ax.text((t2 + t4) / 2, ymax - 0.05 * y_range, 'MATURE', 
                ha='center', va='top', fontsize=9, fontweight='bold', 
                color=stylesheet.COLORS['mature'], alpha=1)
    
    # DECAY region (230 - x7 to 230)
    ax.axvspan(t4, t5, alpha=0.15, color=stylesheet.COLORS['decay'], label='_nolegend_')
    if t5 - t4 > 10:  # Only show text if region is wide enough
        ax.text(t4 + 0.05 * (t5 - t4), ymax - 0.05 * y_range, 'DECAY', 
                ha='left', va='top', fontsize=9, fontweight='bold', 
                color=stylesheet.COLORS['decay'], alpha=1)
    else:
        ax.text((t4 + t5) / 2, ymax - 0.05 * y_range, 'DECAY', 
                ha='center', va='top', fontsize=9, fontweight='bold', 
                color=stylesheet.COLORS['decay'], alpha=1)
    
    # POST-DECAY region (after 230 to end)
    if t5 < xmax:
        ax.axvspan(t5, xmax, alpha=0.15, color=stylesheet.COLORS['strat'], label='_nolegend_')
    
    # ===========================
    # LABELS AND TITLES
    # ===========================
    
    # Create parameter string for title
    param_str = f"x1={params['x1']}, x2={params['x2']}, x3={params['x3']}, x4={params['x4']}, x5={params['x5']}, x6={params['x6']}, x7={params['x7']}"
    ax.set_title(f"Rainfall accumulation from raincell (x7 = {x7} min)\nMature: {t2}-{t4:.0f} min, Decay: {t4:.0f}-{t5} min\n{param_str}", fontsize=10)
    ax.set_xlabel("Time [min]", fontsize=10)
    ax.set_ylabel("Rainfall accumulation [mm/5min]", fontsize=10)
    ax.legend(loc='best', fontsize=8)
    ax.grid(True, linestyle=':', alpha=0.5, linewidth=0.5)
    
    plt.tight_layout()
    
    # Save figure in the same directory as the stats file
    # Get the directory of the stats file
    stats_dir = os.path.dirname(filepath)
    
    # Create 'plots' subdirectory in the same location as the stats files
    plots_dir = os.path.join(stats_dir, 'plots')
    if not os.path.exists(plots_dir):
        os.makedirs(plots_dir)
        print(f"   Created plots directory: {plots_dir}")
    
    # Create filename based on parameters
    filename_base = f"stats_visualization_x1_{params['x1']:03d}_x2_{params['x2']:03d}_x3_{params['x3']:03d}_x4_{params['x4']:02d}_x5_{params['x5']:02d}_x6_{params['x6']:03d}_x7_{params['x7']:03d}"
    
    # Save in plots directory
    pdf_path = os.path.join(plots_dir, f"{filename_base}.pdf")
    png_path = os.path.join(plots_dir, f"{filename_base}.png")

    plt.savefig(pdf_path, bbox_inches='tight')
    plt.savefig(png_path, dpi=300, bbox_inches='tight')
    
    print(f"\n✅ Figure saved as: {pdf_path}")
    print(f"✅ Figure saved as: {png_path}")
    print(f"   Region boundaries:")
    print(f"     UNINITIATED: 0-{t1} min")
    print(f"     GROWTH:      {t1}-{t2} min")
    print(f"     MATURE:      {t2}-{t4:.0f} min")
    print(f"     DECAY:       {t4:.0f}-{t5} min")
    print(f"     POST-DECAY:  {t5}-end")
    
    plt.show()

# ===========================
# MAIN FUNCTION
# ===========================

def main():
    # Check if folder path was provided as command-line argument
    if len(sys.argv) > 1:
        folder_path = sys.argv[1]
    else:
        # Ask for folder path
        print("\n" + "="*50)
        print("  STATS FILE VISUALIZER")
        print("="*50)
        folder_path = input("\nEnter batch test folder path (e.g., batch_test_20260506_155323): ").strip()
        if folder_path == "":
            print("❌ No folder path provided!")
            return
    
    # Check if folder exists
    if not os.path.exists(folder_path):
        print(f"❌ Folder '{folder_path}' does not exist!")
        return
    
    # Show available parameters
    available = show_available_parameters(folder_path)
    if available is None:
        return
    
    # Allow multiple selections
    while True:
        # Get parameter input
        params = get_parameter_input()
        
        # Find the stats file
        filepath = find_stats_file(folder_path, params)
        
        if filepath:
            print(f"\n✅ Found file: {os.path.basename(filepath)}")
            plot_stats(filepath, params)
        else:
            print(f"\n❌ No stats file found for parameters: {params}")
            print("   Please check the parameter values and try again.")
        
        # Ask if user wants to try another
        again = input("\n\nView another combination? (y/n) [n]: ").strip().lower()
        if again != 'y':
            break
    
    print("\n✅ Done!")

# ===========================
# RUN SCRIPT
# ===========================

if __name__ == "__main__":
    main()
