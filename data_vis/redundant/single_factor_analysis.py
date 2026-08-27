import numpy as np
import matplotlib.pyplot as plt
import stylesheet  # Import the stylesheet

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
    
    # Plot histograms with transparency - using stylesheet colors
    ax.hist(emd1, bins=n_bins, alpha=0.6, color=stylesheet.COLORS['blue'], 
            edgecolor='black', linewidth=0.5, label='Strategy 1 (Column 8)', 
            density=True)
    ax.hist(emd2, bins=n_bins, alpha=0.6, color=stylesheet.COLORS['orange'], 
            edgecolor='black', linewidth=0.5, label='Strategy 2 (Column 9)', 
            density=True)
    
    # Add vertical lines for means and medians
    ax.axvline(stats1['mean'], color=stylesheet.COLORS['navy'], linestyle='--', linewidth=2.5,
               label=f'Mean S1: {stats1["mean"]:.6f}')
    ax.axvline(stats1['median'], color=stylesheet.COLORS['blue'], linestyle='-.', linewidth=2,
               label=f'Median S1: {stats1["median"]:.6f}')
    
    ax.axvline(stats2['mean'], color=stylesheet.COLORS['maroon'], linestyle='--', linewidth=2.5,
               label=f'Mean S2: {stats2["mean"]:.6f}')
    ax.axvline(stats2['median'], color=stylesheet.COLORS['red'], linestyle='-.', linewidth=2,
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


def plot_emd_scatter(file_path, save_path=None, alpha=0.6, add_diagonal=True):
    """
    Create a scatter plot comparing EMD values from columns 8 and 9.
    
    Parameters:
    -----------
    file_path : str
        Path to the EMD results file
    save_path : str, optional
        Path to save the figure (if None, displays the plot)
    alpha : float, optional
        Transparency of scatter points (default: 0.6)
    add_diagonal : bool, optional
        Whether to add the y=x diagonal line (default: True)
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
        emd1 = data[:, 7]   # 8th column (Strategy 1)
        emd2 = data[:, 8]   # 9th column (Strategy 2)
        print(f"Extracted {len(emd1)} EMD values from column 8")
        print(f"Extracted {len(emd2)} EMD values from column 9")
    else:
        print(f"Error: File has only {data.shape[1]} columns, expected at least 9")
        return
    
    # Create figure
    fig, ax = plt.subplots(figsize=(10, 8))
    
    # Create scatter plot using stylesheet colors
    scatter = ax.scatter(emd1, emd2, alpha=alpha, s=30, 
                        color=stylesheet.COLORS['blue'],
                        edgecolor='white', linewidth=0.5)
    
    # Add diagonal line (y=x) for reference
    if add_diagonal:
        min_val = min(np.min(emd1), np.min(emd2))
        max_val = max(np.max(emd1), np.max(emd2))
        # Add some padding
        padding = (max_val - min_val) * 0.05
        min_val -= padding
        max_val += padding
        ax.plot([min_val, max_val], [min_val, max_val], 
                color=stylesheet.COLORS['red'], linestyle='--', 
                linewidth=2, alpha=0.7, label='y = x (perfect agreement)')
    
    # Add labels and title
    ax.set_xlabel('EMD Strategy 1 (Column 8)', fontsize=13, fontweight='bold')
    ax.set_ylabel('EMD Strategy 2 (Column 9)', fontsize=13, fontweight='bold')
    ax.set_title('Comparison of EMD Values: Strategy 1 vs Strategy 2', 
                 fontsize=14, fontweight='bold')
    
    # Add grid
    ax.grid(True, alpha=0.3)
    
    # Add legend
    ax.legend(loc='best', fontsize=10)
    
    # Add statistics box
    correlation = np.corrcoef(emd1, emd2)[0, 1]
    diff_mean = np.mean(emd2 - emd1)
    diff_std = np.std(emd2 - emd1)
    
    stats_text = (
        f'Correlation: {correlation:.6f}\n'
        f'Mean Diff (S2-S1): {diff_mean:.6f}\n'
        f'Std Diff (S2-S1): {diff_std:.6f}\n'
        f'Min Diff: {np.min(emd2 - emd1):.6f}\n'
        f'Max Diff: {np.max(emd2 - emd1):.6f}'
    )
    
    ax.text(0.02, 0.98, stats_text, transform=ax.transAxes, fontsize=10,
            verticalalignment='top', 
            bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.9))
    
    plt.tight_layout()
    
    # Save or display
    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        print(f"Figure saved to: {save_path}")
    else:
        plt.show()
    
    # Print additional statistics
    print("\n" + "="*80)
    print("SCATTER PLOT STATISTICS")
    print("="*80)
    print(f"Pearson correlation coefficient: {correlation:.6f}")
    print(f"\nDifference (Strategy 2 - Strategy 1):")
    print(f"  Mean: {diff_mean:.6f}")
    print(f"  Std: {diff_std:.6f}")
    print(f"  Min: {np.min(emd2 - emd1):.6f}")
    print(f"  Max: {np.max(emd2 - emd1):.6f}")
    print(f"  25th percentile: {np.percentile(emd2 - emd1, 25):.6f}")
    print(f"  75th percentile: {np.percentile(emd2 - emd1, 75):.6f}")
    
    return fig


def plot_dual_emd_comparison(file_path, save_dir=None):
    """
    Create both the histogram and scatter plot for comprehensive comparison.
    
    Parameters:
    -----------
    file_path : str
        Path to the EMD results file
    save_dir : str, optional
        Directory to save both figures (if None, displays both plots)
    """
    
    # Generate histogram
    print("\n" + "="*80)
    print("GENERATING HISTOGRAM...")
    print("="*80)
    if save_dir:
        hist_path = f"{save_dir}/dual_emd_histogram.png"
    else:
        hist_path = None
    plot_dual_emd_histogram(file_path, save_path=hist_path)
    
    # Generate scatter plot
    print("\n" + "="*80)
    print("GENERATING SCATTER PLOT...")
    print("="*80)
    if save_dir:
        scatter_path = f"{save_dir}/emd_scatter.png"
    else:
        scatter_path = None
    plot_emd_scatter(file_path, save_path=scatter_path)
    
    return


# ====================================================
# USAGE EXAMPLES
# ====================================================

# 1. Histogram only
plot_dual_emd_histogram("batch_test_20260827_113654/emd_results.txt")

# 2. Scatter plot only
plot_emd_scatter("batch_test_20260827_113654/emd_results.txt")

# 3. Scatter plot with custom transparency and save
# plot_emd_scatter(
#     "batch_test_20260827_102829/emd_results.txt",
#     save_path="emd_scatter.png",
#     alpha=0.4
# )

# 4. Scatter plot without diagonal line
# plot_emd_scatter(
#     "batch_test_20260827_102829/emd_results.txt",
#     add_diagonal=False
# )

# 5. Generate both plots
# plot_dual_emd_comparison(
#     "batch_test_20260827_102829/emd_results.txt",
#     save_dir="./figures"
# )
