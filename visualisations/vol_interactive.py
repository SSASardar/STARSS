import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots

def visualize_volume_rendering_interactive(data):
    """
    Create an interactive 3D volume visualization with plotly
    """
    # Sample data for performance (adjust sample_rate based on your data size)
    sample_rate = max(1, data['num_x'] // 80)  # Use every Nth point
    
    # Create coordinate grids
    X, Y, Z = np.meshgrid(
        data['x'][::sample_rate], 
        data['y'][::sample_rate], 
        data['z'][::sample_rate], 
        indexing='ij'
    )
    
    refl_sampled = data['grid_refl'][::sample_rate, ::sample_rate, ::sample_rate]
    
    # Create interactive volume plot
    fig = go.Figure(data=go.Volume(
        x=X.flatten(),
        y=Y.flatten(),
        z=Z.flatten(),
        value=refl_sampled.flatten(),
        isomin=np.percentile(refl_sampled, 20),  # Show top 80% of values
        isomax=refl_sampled.max(),
        opacity=0.1,  # Transparency level
        surface_count=15,  # Number of isosurfaces
        colorscale='Viridis',
        colorbar=dict(title="Reflectivity (dBZ)"),
        caps=dict(x_show=True, y_show=True, z_show=True)  # Show bounding box
    ))
    
    # Update layout for better interaction
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
            camera=dict(
                eye=dict(x=1.5, y=1.5, z=1.5)  # Initial viewing angle
            ),
            aspectmode='data'  # Preserve aspect ratio
        ),
        width=1000,
        height=800
    )
    
    return fig

# Alternative: Create multiple interactive slices
def visualize_interactive_slices(data):
    """
    Create an interactive dashboard with multiple 2D slices
    """
    # Create a figure with 3 subplots
    fig = make_subplots(
        rows=1, cols=3,
        subplot_titles=('XY Slice (Horizontal)', 'XZ Slice', 'YZ Slice'),
        specs=[[{'type': 'heatmap'}, {'type': 'heatmap'}, {'type': 'heatmap'}]]
    )
    
    # Select middle slices
    mid_z = data['num_PPIs'] // 2
    mid_y = data['num_y'] // 2
    mid_x = data['num_x'] // 2
    
    # XY slice (horizontal plane at middle height)
    fig.add_trace(
        go.Heatmap(
            z=data['grid_refl'][mid_z].T,
            x=data['x'],
            y=data['y'],
            colorscale='Jet',
            colorbar=dict(title="dBZ", x=1.05)
        ),
        row=1, col=1
    )
    
    # XZ slice (vertical plane along Y)
    fig.add_trace(
        go.Heatmap(
            z=data['grid_refl'][:, mid_y, :].T,
            x=data['x'],
            y=data['z'],
            colorscale='Jet',
            showscale=False
        ),
        row=1, col=2
    )
    
    # YZ slice (vertical plane along X)
    fig.add_trace(
        go.Heatmap(
            z=data['grid_refl'][:, :, mid_x],
            x=data['y'],
            y=data['z'],
            colorscale='Jet',
            showscale=False
        ),
        row=1, col=3
    )
    
    fig.update_layout(
        title="Interactive Slices Through Volume",
        width=1200,
        height=500,
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

# Usage example:
if __name__ == "__main__":
    # Read your data
    data = read_vol_scan_binary('outputs/volume_scan_0028.bin')
    
    # Create interactive 3D volume visualization
    fig_volume = visualize_volume_rendering_interactive(data)
    fig_volume.show()  # Opens in browser
    
    # Save as standalone HTML file (can be shared with anyone)
    fig_volume.write_html("3d_volume_visualization.html")
    
    # Create interactive 2D slices dashboard
    fig_slices = visualize_interactive_slices(data)
    fig_slices.show()
    fig_slices.write_html("volume_slices.html")
