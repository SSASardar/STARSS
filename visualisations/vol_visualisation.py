#!/usr/bin/env python3
"""
Complete 3D Volume Scan Visualization Tool
Reads binary output from C program and creates multiple 3D visualizations
"""

import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
import struct
from scipy.ndimage import zoom
import matplotlib.colors as colors
import sys
import os

# Try to import optional libraries
try:
    from skimage import measure
    SKIMAGE_AVAILABLE = True
except ImportError:
    SKIMAGE_AVAILABLE = False
    print("Warning: scikit-image not installed. Isosurface visualization disabled.")
    print("Install with: pip install scikit-image")

try:
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots
    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False
    print("Warning: plotly not installed. Interactive visualizations disabled.")
    print("Install with: pip install plotly")

def read_vol_scan_binary(filename):
    """
    Read volume scan data from binary file created by C code
    
    Parameters:
    filename (str): Path to binary file
    
    Returns:
    dict: Dictionary containing all volume scan data
    """
    if not os.path.exists(filename):
        raise FileNotFoundError(f"File '{filename}' not found. Please run the C program first.")
    
    with open(filename, 'rb') as f:
        # Read header: num_PPIs, num_x, num_y (3 integers)
        header_data = f.read(12)
        if len(header_data) < 12:
            raise ValueError("File too small to contain header")
        num_PPIs, num_x, num_y = struct.unpack('iii', header_data)
        
        # Read parameters: resolution, ref_x, ref_y, ref_z (4 doubles)
        param_data = f.read(32)
        if len(param_data) < 32:
            raise ValueError("File too small to contain parameters")
        resolution, ref_x, ref_y, ref_z = struct.unpack('dddd', param_data)
        
        # Calculate sizes
        ppi_size = num_x * num_y
        total_size = ppi_size * num_PPIs
        
        # Read reflectivity grid
        refl_data = f.read(total_size * 8)
        if len(refl_data) < total_size * 8:
            raise ValueError("File truncated: insufficient reflectivity data")
        grid_refl = np.frombuffer(refl_data, dtype=np.float64)
        
        # Read height grid
        height_data = f.read(total_size * 8)
        if len(height_data) < total_size * 8:
            raise ValueError("File truncated: insufficient height data")
        grid_height = np.frombuffer(height_data, dtype=np.float64)
        
        # Read attenuation grid
        att_data = f.read(total_size * 8)
        if len(att_data) < total_size * 8:
            raise ValueError("File truncated: insufficient attenuation data")
        grid_att = np.frombuffer(att_data, dtype=np.float64)
        
        # Read display grid (projected data)
        display_data = f.read(ppi_size * 8)
        if len(display_data) < ppi_size * 8:
            raise ValueError("File truncated: insufficient display grid data")
        display_grid = np.frombuffer(display_data, dtype=np.float64)
        
        # Read reflectivity at lowest altitude
        ala_data = f.read(ppi_size * 8)
        if len(ala_data) < ppi_size * 8:
            raise ValueError("File truncated: insufficient ALA data")
        refl_ALA = np.frombuffer(ala_data, dtype=np.float64)
        
        # Reshape 3D arrays
        grid_refl = grid_refl.reshape(num_PPIs, num_y, num_x)
        grid_height = grid_height.reshape(num_PPIs, num_y, num_x)
        grid_att = grid_att.reshape(num_PPIs, num_y, num_x)
        display_grid = display_grid.reshape(num_y, num_x)
        refl_ALA = refl_ALA.reshape(num_y, num_x)
        
        # Create coordinate grids
        x = ref_x + np.arange(num_x) * resolution
        y = ref_y + np.arange(num_y) * resolution
        z = ref_z + np.arange(num_PPIs) * resolution
        
        return {
            'num_PPIs': num_PPIs,
            'num_x': num_x,
            'num_y': num_y,
            'resolution': resolution,
            'ref_point': (ref_x, ref_y, ref_z),
            'x': x,
            'y': y,
            'z': z,
            'grid_refl': grid_refl,
            'grid_height': grid_height,
            'grid_att': grid_att,
            'display_grid': display_grid,
            'refl_ALA': refl_ALA
        }

def visualize_3d_scatter(data, threshold_db=10, sample_factor=5):
    """
    Create 3D scatter plot of reflectivity values
    
    Parameters:
    data (dict): Volume scan data
    threshold_db (float): Minimum reflectivity to display
    sample_factor (int): Sample every N points for large datasets
    """
    fig = plt.figure(figsize=(14, 10))
    ax = fig.add_subplot(111, projection='3d')
    
    # Sample data for better performance
    sample_x = slice(0, data['num_x'], sample_factor)
    sample_y = slice(0, data['num_y'], sample_factor)
    sample_z = slice(0, data['num_PPIs'], sample_factor)
    
    # Create meshgrid for 3D points
    X, Y, Z = np.meshgrid(data['x'][sample_x], 
                         data['y'][sample_y], 
                         data['z'][sample_z], 
                         indexing='ij')
    
    refl_sampled = data['grid_refl'][sample_z, sample_y, sample_x]
    
    # Flatten arrays
    X_flat = X.flatten()
    Y_flat = Y.flatten()
    Z_flat = Z.flatten()
    refl_flat = refl_sampled.flatten()
    
    # Filter by threshold
    mask = refl_flat > threshold_db
    if not np.any(mask):
        print(f"Warning: No points above threshold {threshold_db} dBZ. Showing all points.")
        mask = slice(None)
    
    # Create scatter plot
    scatter = ax.scatter(X_flat[mask], Y_flat[mask], Z_flat[mask], 
                        c=refl_flat[mask], cmap='jet', 
                        s=8, alpha=0.6, vmin=threshold_db, vmax=refl_flat.max())
    
    ax.set_xlabel('X (m)', fontsize=12)
    ax.set_ylabel('Y (m)', fontsize=12)
    ax.set_zlabel('Z (m)', fontsize=12)
    ax.set_title(f'3D Volume Scan - Reflectivity (Threshold: {threshold_db} dBZ)', fontsize=14)
    
    cbar = plt.colorbar(scatter, ax=ax, shrink=0.5, aspect=10)
    cbar.set_label('Reflectivity (dBZ)', fontsize=12)
    
    # Set reasonable limits
    ax.set_xlim([data['x'][0], data['x'][-1]])
    ax.set_ylim([data['y'][0], data['y'][-1]])
    ax.set_zlim([data['z'][0], data['z'][-1]])
    
    plt.tight_layout()
    return fig

def visualize_slices(data, num_slices=6):
    """
    Visualize horizontal slices at different altitudes
    
    Parameters:
    data (dict): Volume scan data
    num_slices (int): Number of slices to display
    """
    n_slices = min(num_slices, data['num_PPIs'])
    slice_indices = np.linspace(0, data['num_PPIs']-1, n_slices, dtype=int)
    
    # Calculate grid size for subplots
    cols = min(3, n_slices)
    rows = (n_slices + cols - 1) // cols
    
    fig, axes = plt.subplots(rows, cols, figsize=(5*cols, 4*rows))
    if n_slices == 1:
        axes = np.array([axes])
    axes = axes.flatten()
    
    vmin = np.percentile(data['grid_refl'], 5)
    vmax = np.percentile(data['grid_refl'], 95)
    
    for idx, ax in enumerate(axes):
        if idx < len(slice_indices):
            slice_idx = slice_indices[idx]
            im = ax.imshow(data['grid_refl'][slice_idx].T, 
                          origin='lower', 
                          extent=[data['x'][0], data['x'][-1], 
                                 data['y'][0], data['y'][-1]],
                          cmap='jet', 
                          vmin=vmin, vmax=vmax,
                          aspect='auto')
            ax.set_title(f'Altitude Z = {data["z"][slice_idx]:.1f} m', fontsize=10)
            ax.set_xlabel('X (m)', fontsize=9)
            ax.set_ylabel('Y (m)', fontsize=9)
            ax.grid(True, alpha=0.3)
        else:
            ax.axis('off')
    
    # Add colorbar
    plt.colorbar(im, ax=axes, label='Reflectivity (dBZ)', shrink=0.8)
    plt.suptitle('Horizontal Slices Through Volume Scan', fontsize=14, y=1.02)
    plt.tight_layout()
    return fig

def visualize_isosurface(data, iso_value=20):
    """
    Create isosurface visualization using marching cubes
    
    Parameters:
    data (dict): Volume scan data
    iso_value (float): Reflectivity threshold for isosurface
    """
    if not SKIMAGE_AVAILABLE:
        print("Cannot create isosurface: scikit-image not installed")
        return None
    
    fig = plt.figure(figsize=(12, 10))
    ax = fig.add_subplot(111, projection='3d')
    
    # Apply smoothing and find isosurface
    refl_data = data['grid_refl']
    
    try:
        # Find isosurface
        verts, faces, _, _ = measure.marching_cubes(refl_data, iso_value)
        
        # Scale vertices to real coordinates
        verts[:, 0] = data['x'][0] + verts[:, 0] * data['resolution']
        verts[:, 1] = data['y'][0] + verts[:, 1] * data['resolution']
        verts[:, 2] = data['z'][0] + verts[:, 2] * data['resolution']
        
        # Create mesh collection
        mesh = Poly3DCollection(verts[faces], alpha=0.6, linewidth=0.1, edgecolor='black')
        
        # Color based on Z-value or reflectivity
        face_colors = []
        for face in faces:
            center_z = np.mean(verts[face, 2])
            face_colors.append(plt.cm.viridis(center_z / data['z'][-1]))
        
        mesh.set_facecolor(face_colors)
        mesh.set_alpha(0.7)
        ax.add_collection3d(mesh)
        
        ax.set_xlabel('X (m)', fontsize=12)
        ax.set_ylabel('Y (m)', fontsize=12)
        ax.set_zlabel('Z (m)', fontsize=12)
        ax.set_title(f'Isosurface at {iso_value} dBZ', fontsize=14)
        
        # Set limits
        ax.set_xlim([data['x'][0], data['x'][-1]])
        ax.set_ylim([data['y'][0], data['y'][-1]])
        ax.set_zlim([data['z'][0], data['z'][-1]])
        
        # Add colorbar
        sm = plt.cm.ScalarMappable(cmap=plt.cm.viridis, 
                                   norm=plt.Normalize(vmin=data['z'][0], vmax=data['z'][-1]))
        sm.set_array([])
        cbar = plt.colorbar(sm, ax=ax, shrink=0.5, aspect=10)
        cbar.set_label('Altitude (m)', fontsize=12)
        
    except Exception as e:
        print(f"Error creating isosurface: {e}")
        ax.text2D(0.5, 0.5, f"No isosurface found at {iso_value} dBZ", 
                 transform=ax.transAxes, ha='center', fontsize=14)
    
    plt.tight_layout()
    return fig

def visualize_vertical_slice(data, slice_type='x', slice_index=None):
    """
    Create vertical slice visualization
    
    Parameters:
    data (dict): Volume scan data
    slice_type (str): 'x' for constant X, 'y' for constant Y
    slice_index (int): Index of the slice (if None, uses middle)
    """
    fig = plt.figure(figsize=(12, 8))
    
    if slice_type == 'x':
        if slice_index is None:
            slice_index = data['num_x'] // 2
        slice_data = data['grid_refl'][:, :, slice_index]
        x_coords = data['z']
        y_coords = data['y']
        xlabel = 'Z (m)'
        ylabel = 'Y (m)'
        title = f'Vertical Slice at X = {data["x"][slice_index]:.1f} m'
    else:  # 'y' slice
        if slice_index is None:
            slice_index = data['num_y'] // 2
        slice_data = data['grid_refl'][:, slice_index, :]
        x_coords = data['z']
        y_coords = data['x']
        xlabel = 'Z (m)'
        ylabel = 'X (m)'
        title = f'Vertical Slice at Y = {data["y"][slice_index]:.1f} m'
    
    im = plt.imshow(slice_data.T, origin='lower', 
                   extent=[x_coords[0], x_coords[-1], y_coords[0], y_coords[-1]],
                   cmap='jet', aspect='auto')
    
    plt.xlabel(xlabel, fontsize=12)
    plt.ylabel(ylabel, fontsize=12)
    plt.title(title, fontsize=14)
    plt.colorbar(im, label='Reflectivity (dBZ)')
    plt.grid(True, alpha=0.3)
    
    plt.tight_layout()
    return fig

def visualize_maximum_intensity_projection(data):
    """
    Create maximum intensity projection (MIP) visualization
    Shows maximum reflectivity along vertical direction
    """
    fig, axes = plt.subplots(1, 2, figsize=(14, 6))
    
    # Maximum intensity projection (along Z)
    mip_z = np.max(data['grid_refl'], axis=0)
    
    im1 = axes[0].imshow(mip_z.T, origin='lower',
                        extent=[data['x'][0], data['x'][-1], 
                               data['y'][0], data['y'][-1]],
                        cmap='jet', aspect='auto')
    axes[0].set_title('Maximum Intensity Projection (Top View)', fontsize=12)
    axes[0].set_xlabel('X (m)')
    axes[0].set_ylabel('Y (m)')
    plt.colorbar(im1, ax=axes[0], label='Max Reflectivity (dBZ)')
    
    # Maximum intensity projection along X
    mip_x = np.max(data['grid_refl'], axis=2)
    
    im2 = axes[1].imshow(mip_x.T, origin='lower',
                        extent=[data['y'][0], data['y'][-1], 
                               data['z'][0], data['z'][-1]],
                        cmap='jet', aspect='auto')
    axes[1].set_title('Maximum Intensity Projection (Side View)', fontsize=12)
    axes[1].set_xlabel('Y (m)')
    axes[1].set_ylabel('Z (m)')
    plt.colorbar(im2, ax=axes[1], label='Max Reflectivity (dBZ)')
    
    plt.suptitle('Maximum Intensity Projections', fontsize=14, y=1.02)
    plt.tight_layout()
    return fig

def visualize_plotly_volume_rendering(data):
    """
    Create interactive 3D volume visualization with plotly
    """
    if not PLOTLY_AVAILABLE:
        print("Cannot create plotly visualization: plotly not installed")
        return None
    
    # Sample data for performance
    sample_rate = max(1, min(data['num_x'], data['num_y'], data['num_PPIs']) // 80)
    
    X, Y, Z = np.meshgrid(data['x'][::sample_rate], 
                         data['y'][::sample_rate], 
                         data['z'][::sample_rate], 
                         indexing='ij')
    
    refl_sampled = data['grid_refl'][::sample_rate, ::sample_rate, ::sample_rate]
    
    # Create interactive volume plot
    fig = go.Figure(data=go.Volume(
        x=X.flatten(),
        y=Y.flatten(),
        z=Z.flatten(),
        value=refl_sampled.flatten(),
        isomin=np.percentile(refl_sampled, 20),
        isomax=refl_sampled.max(),
        opacity=0.1,
        surface_count=15,
        colorscale='Viridis',
        colorbar=dict(title="Reflectivity (dBZ)"),
        caps=dict(x_show=True, y_show=True, z_show=True)
    ))
    
    fig.update_layout(
        title={
            'text': "Interactive 3D Volume Scan - Reflectivity",
            'x': 0.5,
            'xanchor': 'center'
        },
        scene=dict(
            xaxis_title='X (m)',
            yaxis_title='Y (m)',
            zaxis_title='Z (m)',
            camera=dict(eye=dict(x=1.5, y=1.5, z=1.5)),
            aspectmode='data'
        ),
        width=1000,
        height=800
    )
    
    return fig

def visualize_plotly_slices(data):
    """
    Create interactive dashboard with multiple 2D slices using plotly
    """
    if not PLOTLY_AVAILABLE:
        print("Cannot create plotly slices: plotly not installed")
        return None
    
    # Select middle slices
    mid_z = data['num_PPIs'] // 2
    mid_y = data['num_y'] // 2
    mid_x = data['num_x'] // 2
    
    # Create figure with 3 subplots
    fig = make_subplots(
        rows=1, cols=3,
        subplot_titles=('XY Slice (Horizontal)', 'XZ Slice (Vertical - Y constant)', 
                       'YZ Slice (Vertical - X constant)'),
        specs=[[{'type': 'heatmap'}, {'type': 'heatmap'}, {'type': 'heatmap'}]]
    )
    
    # XY slice (horizontal plane at middle height)
    fig.add_trace(
        go.Heatmap(
            z=data['grid_refl'][mid_z].T,
            x=data['x'],
            y=data['y'],
            colorscale='Jet',
            colorbar=dict(title="dBZ", x=1.05),
            hovertemplate='X: %{x:.1f}m<br>Y: %{y:.1f}m<br>Reflectivity: %{z:.1f}dBZ<extra></extra>'
        ),
        row=1, col=1
    )
    
    # XZ slice (vertical plane along Y at middle)
    fig.add_trace(
        go.Heatmap(
            z=data['grid_refl'][:, mid_y, :].T,
            x=data['x'],
            y=data['z'],
            colorscale='Jet',
            showscale=False,
            hovertemplate='X: %{x:.1f}m<br>Z: %{y:.1f}m<br>Reflectivity: %{z:.1f}dBZ<extra></extra>'
        ),
        row=1, col=2
    )
    
    # YZ slice (vertical plane along X at middle)
    fig.add_trace(
        go.Heatmap(
            z=data['grid_refl'][:, :, mid_x],
            x=data['y'],
            y=data['z'],
            colorscale='Jet',
            showscale=False,
            hovertemplate='Y: %{x:.1f}m<br>Z: %{y:.1f}m<br>Reflectivity: %{z:.1f}dBZ<extra></extra>'
        ),
        row=1, col=3
    )
    
    fig.update_layout(
        title="Interactive Slices Through Volume",
        width=1400,
        height=550,
        showlegend=False
    )
    
    # Update axes labels
    fig.update_xaxes(title_text="X (m)", row=1, col=1)
    fig.update_yaxes(title_text="Y (m)", row=1, col=1)
    fig.update_xaxes(title_text="X (m)", row=1, col=2)
    fig.update_yaxes(title_text="Z (m)", row=1, col=2)
    fig.update_xaxes(title_text="Y (m)", row=1, col=3)
    fig.update_yaxes(title_text="Z (m)", row=1, col=3)
    
    return fig

def print_data_summary(data):
    """
    Print summary information about the volume scan data
    """
    print("\n" + "="*60)
    print("VOLUME SCAN DATA SUMMARY")
    print("="*60)
    print(f"Dimensions:        {data['num_x']} x {data['num_y']} x {data['num_PPIs']} (X x Y x Z)")
    print(f"Total grid points: {data['num_x'] * data['num_y'] * data['num_PPIs']:,}")
    print(f"Resolution:        {data['resolution']:.2f} m")
    print(f"X range:          [{data['x'][0]:.1f}, {data['x'][-1]:.1f}] m")
    print(f"Y range:          [{data['y'][0]:.1f}, {data['y'][-1]:.1f}] m")
    print(f"Z range:          [{data['z'][0]:.1f}, {data['z'][-1]:.1f}] m")
    print(f"\nReflectivity (dBZ):")
    print(f"  Min:            {data['grid_refl'].min():.2f}")
    print(f"  Max:            {data['grid_refl'].max():.2f}")
    print(f"  Mean:           {data['grid_refl'].mean():.2f}")
    print(f"  Std dev:        {data['grid_refl'].std():.2f}")
    print(f"\nAttenuation (dB):")
    print(f"  Min:            {data['grid_att'].min():.2f}")
    print(f"  Max:            {data['grid_att'].max():.2f}")
    print(f"  Mean:           {data['grid_att'].mean():.2f}")
    print("="*60 + "\n")

def main():
    """
    Main function to run all visualizations
    """
    # Read the binary file
    try:
        data = read_vol_scan_binary('outputs/volume_scan_0028.bin')
        print("✓ Successfully loaded volume scan data")
        print_data_summary(data)
        
        # Create output directory for figures
        output_dir = "volume_visualizations"
        os.makedirs(output_dir, exist_ok=True)
        
        # 1. 3D Scatter Plot
        print("Creating 3D scatter plot...")
        fig1 = visualize_3d_scatter(data, threshold_db=10, sample_factor=3)
        fig1.savefig(f"{output_dir}/3d_scatter.png", dpi=150, bbox_inches='tight')
        plt.close(fig1)
        print(f"  ✓ Saved to {output_dir}/3d_scatter.png")
        
        # 2. Horizontal Slices
        print("Creating horizontal slices...")
        fig2 = visualize_slices(data, num_slices=6)
        fig2.savefig(f"{output_dir}/horizontal_slices.png", dpi=150, bbox_inches='tight')
        plt.close(fig2)
        print(f"  ✓ Saved to {output_dir}/horizontal_slices.png")
        
        # 3. Isosurface (if available)
        if SKIMAGE_AVAILABLE:
            print("Creating isosurface visualization...")
            fig3 = visualize_isosurface(data, iso_value=20)
            if fig3:
                fig3.savefig(f"{output_dir}/isosurface.png", dpi=150, bbox_inches='tight')
                plt.close(fig3)
                print(f"  ✓ Saved to {output_dir}/isosurface.png")
        else:
            print("  ⚠ Skipping isosurface (scikit-image not installed)")
        
        # 4. Vertical Slices
        print("Creating vertical slices...")
        fig4 = visualize_vertical_slice(data, slice_type='x')
        fig4.savefig(f"{output_dir}/vertical_slice_x.png", dpi=150, bbox_inches='tight')
        plt.close(fig4)
        
        fig5 = visualize_vertical_slice(data, slice_type='y')
        fig5.savefig(f"{output_dir}/vertical_slice_y.png", dpi=150, bbox_inches='tight')
        plt.close(fig5)
        print(f"  ✓ Saved to {output_dir}/vertical_slice_x.png and vertical_slice_y.png")
        
        # 5. Maximum Intensity Projection
        print("Creating maximum intensity projections...")
        fig6 = visualize_maximum_intensity_projection(data)
        fig6.savefig(f"{output_dir}/mip_projections.png", dpi=150, bbox_inches='tight')
        plt.close(fig6)
        print(f"  ✓ Saved to {output_dir}/mip_projections.png")
        
        # 6. Interactive Plotly Visualizations
        if PLOTLY_AVAILABLE:
            print("Creating interactive Plotly visualizations...")
            
            # Volume rendering
            fig7 = visualize_plotly_volume_rendering(data)
            if fig7:
                fig7.write_html(f"{output_dir}/interactive_volume.html")
                print(f"  ✓ Saved to {output_dir}/interactive_volume.html")
            
            # Interactive slices
            fig8 = visualize_plotly_slices(data)
            if fig8:
                fig8.write_html(f"{output_dir}/interactive_slices.html")
                print(f"  ✓ Saved to {output_dir}/interactive_slices.html")
        else:
            print("  ⚠ Skipping interactive visualizations (plotly not installed)")
        
        print(f"\n✓ All visualizations saved to '{output_dir}/' directory")
        print("\nTo view the visualizations:")
        print("  - Open the PNG files with any image viewer")
        print("  - Open the HTML files in a web browser for interactive views")
        
        # Optionally display one figure
        show_interactive = input("\nDo you want to open the interactive HTML visualization in your browser? (y/n): ").lower()
        if show_interactive == 'y' and PLOTLY_AVAILABLE:
            import webbrowser
            webbrowser.open(f"{output_dir}/interactive_volume.html")
        
    except FileNotFoundError as e:
        print(f"Error: {e}")
        print("\nMake sure you have run the C program first to generate 'volume_scan.bin'")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
