"""
View saved point cloud scans.
Requires: pip3 install open3d
"""
import numpy as np
import sys

try:
    import open3d as o3d
except ImportError:
    print("open3d not installed. Install with: pip3 install open3d")
    sys.exit(1)

# Load saved scan
scan_file = 'scan.npz'
if len(sys.argv) > 1:
    scan_file = sys.argv[1]

try:
    data = np.load(scan_file)
    vertices = data['vertices']
    color_image = data['color_image']
    
    print(f"Loaded scan: {scan_file}")
    print(f"Points: {len(vertices)}")
    print(f"Color image shape: {color_image.shape}")
    
    # Filter out invalid points (zeros or NaN)
    valid_mask = ~np.isnan(vertices).any(axis=1) & (vertices != 0).any(axis=1)
    vertices = vertices[valid_mask]
    
    print(f"Valid points: {len(vertices)}")
    
    # Create point cloud
    pcd = o3d.geometry.PointCloud()
    pcd.points = o3d.utility.Vector3dVector(vertices)
    
    # Color points (simplified - for full color mapping, you'd need texture coordinates)
    # You can also use depth-based coloring
    if len(vertices) > 0:
        # Color by Z-depth (distance from camera)
        z_values = vertices[:, 2]
        z_normalized = (z_values - z_values.min()) / (z_values.max() - z_values.min() + 1e-6)
        colors = np.zeros((len(vertices), 3))
        colors[:, 0] = z_normalized  # Red channel based on depth
        colors[:, 2] = 1 - z_normalized  # Blue channel (inverse)
        pcd.colors = o3d.utility.Vector3dVector(colors)
    
    # Visualize
    print("Opening 3D viewer. Close window to exit.")
    o3d.visualization.draw_geometries([pcd],
                                     window_name="Point Cloud Viewer",
                                     width=800,
                                     height=600)
    
except FileNotFoundError:
    print(f"Scan file '{scan_file}' not found.")
    print("First capture a scan using: python3 point_cloud_capture.py")
except Exception as e:
    print(f"Error loading scan: {e}")
