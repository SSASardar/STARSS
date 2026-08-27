import numpy as np
import matplotlib.pyplot as plt
from scipy import stats

def plot_dual_emd_histogram(file_path, save_path=None, bins=30):
    """
    Plot overlaid histograms of EMD values from columns 8 and 9.
    
    Parameters:
    -----------
    file_path : str
        Path to the EMD results file
    save_path : str, optional
        Path to save the figure (if None, displays the plot)
    bins : int, optional
        Number of bins for the histogram (default: 30)
    """
    
    # Load the data
    try:
        data = np.loadtxt(file_path, comments="#")
        print(f"Loaded data: {data.shape[0]} rows, {data.shape[1]} columns")
    except FileNotFoundError:
        print(f"Error: Could not find '{file_path}'")
        return
    except Exception as e:
        print(f"Error loading file: {e}")
        return
    
    # Extract EMD values (8th column = index 7, 9th column = index 8)
    if data.shape[1] >= 9:
        emd1 = data[:, 7]   # 8th column
        emd2 = data[:, 8]   # 9th column
        print(f"Extracted {len(emd1)} EMD values from column 8")
        print(f"Extracted {len(emd2)} EMD values from column 9")
    else:
        print(f"Error: File has only {data.shape[1]} columns, expected at least 9")
        return
    
    # Calculate statistics
    stats1 = {
        'mean': np.mean(emd1),
        'median': np.median(emd1),
        'std': np.std(emd1),
        'min': np.min(emd1),
        'max': np.max(emd1)
    }
    
    stats2 = {
        'mean': np.mean(emd2),
        'median': np.median(emd2),
        'std': np.std(emd2),
        'min': np.min(emd2),
        'max': np.max(emd2)
    }
    
    # Create figure
    fig, ax = plt.subplots(figsize=(12, 7))
    
    # Determine optimal bin width using Freedman-Diaconis rule
    all_values = np.concatenate([emd1, emd2])
    iqr = np.percentile(all_values, 75) - np.percentile(all_values, 25)
    bin_width = 2 * iqr / (len(all_values) ** (1/3)) if iqr > 0 else 1
    n_bins = int(np.ceil((np.max(all_values) - np.min(all_values)) / bin_width))
    n_bins = max(20, min(50, n_bins))  # Clamp between 20 and 50 bins
    
    # Plot histograms with transparency
    ax.hist(emd1, bins=n_bins, alpha=0.6, color='steelblue', 
            edgecolor='black', linewidth=0.5, label='Strategy 1 (Column 8)', 
            density=True)
    ax.hist(emd2, bins=n_bins, alpha=0.6, color='salmon', 
            edgecolor='black', linewidth=0.5, label='Strategy 2 (Column 9)', 
            density=True)
    
    # Add vertical lines for means and medians
    ax.axvline(stats1['mean'], color='darkblue', linestyle='--', linewidth=2.5,
               label=f'Mean S1: {stats1["mean"]:.6f}')
    ax.axvline(stats1['median'], color='blue', linestyle='-.', linewidth=2,
               label=f'Median S1: {stats1["median"]:.6f}')
    
    ax.axvline(stats2['mean'], color='darkred', linestyle='--', linewidth=2.5,
               label=f'Mean S2: {stats2["mean"]:.6f}')
    ax.axvline(stats2['median'], color='red', linestyle='-.', linewidth=2,
               label=f'Median S2: {stats2["median"]:.6f}')
    
    # Add labels and title
    ax.set_xlabel('EMD Value', fontsize=13, fontweight='bold')
    ax.set_ylabel('Density', fontsize=13, fontweight='bold')
    ax.set_title('EMD Distribution: Two Scanning Strategies', fontsize=14, fontweight='bold')
    ax.grid(True, alpha=0.3)
    ax.legend(loc='upper right', fontsize=10)
    
   
   
    plt.tight_layout()
    
    # Save or display
    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        print(f"Figure saved to: {save_path}")
    else:
        plt.show()
    
    # Print detailed statistics
    print("\n" + "="*80)
    print("DETAILED STATISTICS")
    print("="*80)
    print(f"{'Statistic':<20} {'Strategy 1 (Col 8)':<22} {'Strategy 2 (Col 9)':<22}")
    print("-"*64)
    print(f"{'Count':<20} {len(emd1):<22} {len(emd2):<22}")
    print(f"{'Mean':<20} {stats1['mean']:<22.6f} {stats2['mean']:<22.6f}")
    print(f"{'Median':<20} {stats1['median']:<22.6f} {stats2['median']:<22.6f}")
    print(f"{'Std Dev':<20} {stats1['std']:<22.6f} {stats2['std']:<22.6f}")
    print(f"{'Min':<20} {stats1['min']:<22.6f} {stats2['min']:<22.6f}")
    print(f"{'Max':<20} {stats1['max']:<22.6f} {stats2['max']:<22.6f}")
    print(f"{'Range':<20} {stats1['max']-stats1['min']:<22.6f} {stats2['max']-stats2['min']:<22.6f}")
    print(f"{'25th %ile':<20} {np.percentile(emd1, 25):<22.6f} {np.percentile(emd2, 25):<22.6f}")
    print(f"{'75th %ile':<20} {np.percentile(emd1, 75):<22.6f} {np.percentile(emd2, 75):<22.6f}")
    print(f"{'IQR':<20} {np.percentile(emd1, 75)-np.percentile(emd1, 25):<22.6f} {np.percentile(emd2, 75)-np.percentile(emd2, 25):<22.6f}")
    print("-"*64)
    print(f"{'Mean Diff (S2-S1)':<20} {stats2['mean'] - stats1['mean']:<22.6f}")
    print(f"{'Median Diff (S2-S1)':<20} {stats2['median'] - stats1['median']:<22.6f}")
    print(f"{'Std Diff (S2-S1)':<20} {stats2['std'] - stats1['std']:<22.6f}")
    
   
    return fig


# ====================================================
# USAGE EXAMPLES
# ====================================================

# Basic usage - overlay histograms from columns 8 and 9
plot_dual_emd_histogram("batch_test_20260827_102829/emd_results.txt")

# Save the figure
#plot_dual_emd_histogram(
#    "batch_test_20260825_100749/emd_results.txt",
#    save_path="dual_emd_histogram.png"
#)

# Custom number of bins
#plot_dual_emd_histogram(
#    "batch_test_20260825_100749/emd_results.txt",
#    bins=50
#)
