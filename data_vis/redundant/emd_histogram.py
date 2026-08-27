import numpy as np
import matplotlib.pyplot as plt

def plot_emd_histogram(file_path, save_path=None, bins=30):
    """
    Plot a histogram of EMD values from the results file.
    
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
    
    # Extract EMD values (7th column, index 6)
    if data.shape[1] >= 7:
        emd_values = data[:, 7]  # 8th column
        #emd_values = np.log1p(data[:, 7])  # 8th column with transform for normal distr.
        print(f"Extracted {len(emd_values)} EMD values")
    else:
        print(f"Error: File has only {data.shape[1]} columns, expected at least 7")
        return
    
    # Calculate statistics
    mean_emd = np.mean(emd_values)
    median_emd = np.median(emd_values)
    std_emd = np.std(emd_values)
    min_emd = np.min(emd_values)
    max_emd = np.max(emd_values)
    
    # Create the figure
    fig, ax = plt.subplots(figsize=(10, 6))
    
    # Plot histogram
    n, bins_edges, patches = ax.hist(emd_values, bins=bins, color='steelblue', 
                                      alpha=0.7, edgecolor='black', linewidth=0.5)
    
    # Add vertical lines for statistics
    ax.axvline(mean_emd, color='darkblue', linestyle='--', linewidth=2.5, 
               label=f'Mean: {mean_emd:.6f}')
    ax.axvline(median_emd, color='red', linestyle='-.', linewidth=2, 
               label=f'Median: {median_emd:.6f}')
    
    # Add labels and title
    ax.set_xlabel('EMD Value', fontsize=12, fontweight='bold')
    ax.set_ylabel('Frequency', fontsize=12, fontweight='bold')
    ax.set_title('Distribution of EMD Values', fontsize=14, fontweight='bold')
    ax.grid(True, alpha=0.3)
    ax.legend(loc='upper right', fontsize=10)
    
    # Add statistics box
    stats_text = (
        f'Count: {len(emd_values)}\n'
        f'Mean: {mean_emd:.6f}\n'
        f'Median: {median_emd:.6f}\n'
        f'Std Dev: {std_emd:.6f}\n'
        f'Min: {min_emd:.6f}\n'
        f'Max: {max_emd:.6f}\n'
        f'Range: {max_emd - min_emd:.6f}'
    )
    
    ax.text(0.02, 0.98, stats_text, transform=ax.transAxes, fontsize=10,
            verticalalignment='top', 
            bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))
    
    plt.tight_layout()
    
    # Save or display
    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        print(f"Figure saved to: {save_path}")
    else:
        plt.show()
    
    # Print summary statistics
    print("\n" + "="*60)
    print("SUMMARY STATISTICS")
    print("="*60)
    print(f"Count:              {len(emd_values)}")
    print(f"Mean:               {mean_emd:.6f}")
    print(f"Median:             {median_emd:.6f}")
    print(f"Standard Deviation: {std_emd:.6f}")
    print(f"Minimum:            {min_emd:.6f}")
    print(f"Maximum:            {max_emd:.6f}")
    print(f"Range:              {max_emd - min_emd:.6f}")
    print(f"25th Percentile:    {np.percentile(emd_values, 25):.6f}")
    print(f"75th Percentile:    {np.percentile(emd_values, 75):.6f}")
    print(f"IQR:                {np.percentile(emd_values, 75) - np.percentile(emd_values, 25):.6f}")
    
    return fig

# ====================================================
# USAGE EXAMPLES
# ====================================================

# Basic usage - just display the histogram
plot_emd_histogram("batch_test_20260825_100749/emd_results.txt")

# Save the histogram to a file
#plot_emd_histogram(
#    "batch_test_20260825_100749/emd_results.txt",
#    save_path="emd_histogram.png"
#)

# Use more or fewer bins
#plot_emd_histogram(
#    "batch_test_20260825_100749/emd_results.txt",
#    bins=50
#)

# If your file has a different name or location
#plot_emd_histogram("path/to/your/emd_results.txt")
