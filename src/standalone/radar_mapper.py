"""
3D Radar Mapper - Live occupancy grid and point cloud visualization
Creates a radar-like top-down view with real-time 3D mapping
"""
import pyrealsense2 as rs
import numpy as np
import cv2
import time
from collections import deque

# Try to release any existing pipeline connections
ctx = rs.context()
devices = ctx.query_devices()
if len(devices) > 0:
    print(f"Found RealSense device: {devices[0].get_info(rs.camera_info.name)}")

pipeline = rs.pipeline()
config = rs.config()
config.enable_stream(rs.stream.color, 640, 480, rs.format.bgr8, 30)
config.enable_stream(rs.stream.depth, 640, 480, rs.format.z16, 30)

# Try to start pipeline with retry logic
max_retries = 3
retry_delay = 2

for attempt in range(max_retries):
    try:
        pipeline.start(config)
        print("Camera started successfully!")
        break
    except RuntimeError as e:
        if "busy" in str(e).lower() or "errno=16" in str(e):
            if attempt < max_retries - 1:
                print(f"Camera busy (attempt {attempt + 1}/{max_retries}). Waiting {retry_delay}s...")
                time.sleep(retry_delay)
                try:
                    pipeline.stop()
                except:
                    pass
                pipeline = rs.pipeline()
            else:
                print(f"Error starting camera: {e}")
                exit(1)
        else:
            print(f"Error starting camera: {e}")
            exit(1)

# Create point cloud processor
pc = rs.pointcloud()
align_to = rs.align(rs.stream.color)

# Occupancy grid parameters
grid_size = 400  # pixels (top-down view)
grid_resolution = 0.02  # meters per pixel (2cm resolution)
grid_center = grid_size // 2
max_range = (grid_size // 2) * grid_resolution  # Maximum range in meters

# 3D point storage (world coordinates)
world_points = deque(maxlen=50000)  # Keep last 50k points
point_colors = deque(maxlen=50000)

# Camera pose (simple tracking)
camera_x, camera_y, camera_z = 0.0, 0.0, 0.0
camera_angle = 0.0  # Simple rotation tracking

# Occupancy grid (0=unknown, 1=occupied, 2=free)
occupancy_grid = np.zeros((grid_size, grid_size), dtype=np.uint8)
grid_confidence = np.zeros((grid_size, grid_size), dtype=np.float32)

try:
    print("\n3D Radar Mapper started!")
    print("Controls:")
    print("  'q' - Quit")
    print("  'c' - Clear map")
    print("  's' - Save point cloud")
    print("Move the camera to build the map")
    
    frame_count = 0
    
    while True:
        frames = pipeline.wait_for_frames()
        aligned_frames = align_to.process(frames)
        
        depth_frame = aligned_frames.get_depth_frame()
        color_frame = aligned_frames.get_color_frame()
        
        if not depth_frame or not color_frame:
            continue
        
        # Get camera intrinsics
        depth_intrinsics = depth_frame.profile.as_video_stream_profile().intrinsics
        
        # Generate point cloud
        points = pc.calculate(depth_frame)
        pc.map_to(color_frame)
        
        # Get point cloud data
        vertices = np.asanyarray(points.get_vertices()).view(np.float32).reshape(-1, 3)
        colors = np.asanyarray(points.get_texture_coordinates()).view(np.float32).reshape(-1, 2)
        color_image = np.asanyarray(color_frame.get_data())
        depth_image = np.asanyarray(depth_frame.get_data())
        
        # Filter valid points
        valid_mask = ~np.isnan(vertices).any(axis=1) & (vertices != 0).any(axis=1)
        valid_vertices = vertices[valid_mask]
        
        # Transform points to world coordinates (simple - camera at origin for now)
        # In a full SLAM system, you'd apply camera pose transformation here
        world_vertices = valid_vertices.copy()
        
        # Add to world map
        if len(world_vertices) > 0:
            # Sample points (don't add all to avoid memory issues)
            sample_indices = np.random.choice(len(world_vertices), 
                                            min(1000, len(world_vertices)), 
                                            replace=False)
            sampled_points = world_vertices[sample_indices]
            
            for point in sampled_points:
                world_points.append(point)
                # Get color from texture coordinates (simplified)
                point_colors.append([128, 128, 128])  # Gray default
        
        # Update occupancy grid (top-down view)
        # Project 3D points to 2D grid (X-Y plane, Z is height)
        for point in world_vertices[:500]:  # Sample for performance
            x, y, z = point
            
            # Convert to grid coordinates (top-down view)
            grid_x = int(grid_center + x / grid_resolution)
            grid_y = int(grid_center - y / grid_resolution)  # Flip Y for display
            
            # Check bounds
            if 0 <= grid_x < grid_size and 0 <= grid_y < grid_size:
                # Check if point is within range
                distance = np.sqrt(x**2 + y**2)
                if distance < max_range:
                    # Mark as occupied
                    occupancy_grid[grid_y, grid_x] = 1
                    grid_confidence[grid_y, grid_x] = min(1.0, grid_confidence[grid_y, grid_x] + 0.1)
        
        # Create visualization
        vis_width, vis_height = 1200, 1200
        
        # Top-down radar view (occupancy grid)
        radar_view = np.zeros((grid_size, grid_size, 3), dtype=np.uint8)
        
        # Draw grid
        for i in range(0, grid_size, 20):
            cv2.line(radar_view, (i, 0), (i, grid_size), (20, 20, 20), 1)
            cv2.line(radar_view, (0, i), (grid_size, i), (20, 20, 20), 1)
        
        # Draw occupancy
        occupied_mask = occupancy_grid == 1
        radar_view[occupied_mask] = [0, 255, 0]  # Green for occupied
        
        # Draw with confidence (fade effect)
        for y in range(grid_size):
            for x in range(grid_size):
                if grid_confidence[y, x] > 0:
                    intensity = int(grid_confidence[y, x] * 255)
                    radar_view[y, x] = [0, intensity, 0]
        
        # Draw range circles
        for r in range(1, 6):
            radius = int(r * max_range / 5 / grid_resolution)
            cv2.circle(radar_view, (grid_center, grid_center), radius, (50, 50, 50), 1)
        
        # Draw center (camera position)
        cv2.circle(radar_view, (grid_center, grid_center), 5, (0, 0, 255), -1)
        cv2.circle(radar_view, (grid_center, grid_center), 3, (255, 255, 255), -1)
        
        # Draw direction indicator
        direction_length = 30
        end_x = int(grid_center + direction_length * np.cos(camera_angle))
        end_y = int(grid_center - direction_length * np.sin(camera_angle))
        cv2.line(radar_view, (grid_center, grid_center), (end_x, end_y), (255, 0, 0), 2)
        
        # Add text overlay
        cv2.putText(radar_view, "TOP-DOWN RADAR VIEW", (10, 30), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        cv2.putText(radar_view, f"Points: {len(world_points)}", (10, 60), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        cv2.putText(radar_view, f"Range: {max_range:.1f}m", (10, 80), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        
        # Resize radar view for display
        radar_display = cv2.resize(radar_view, (600, 600))
        
        # Create side view (X-Z plane)
        side_view = np.zeros((grid_size, grid_size, 3), dtype=np.uint8)
        
        # Draw side view occupancy
        for point in list(world_points)[-5000:]:  # Last 5k points
            x, z = point[0], point[2]
            grid_x = int(grid_center + x / grid_resolution)
            grid_z = int(grid_center - z / grid_resolution)
            
            if 0 <= grid_x < grid_size and 0 <= grid_z < grid_size:
                distance = np.sqrt(x**2)
                if distance < max_range:
                    cv2.circle(side_view, (grid_x, grid_z), 1, (0, 255, 0), -1)
        
        # Draw ground line
        cv2.line(side_view, (0, grid_center), (grid_size, grid_center), (100, 100, 100), 1)
        
        # Draw camera position
        cv2.circle(side_view, (grid_center, grid_center), 5, (0, 0, 255), -1)
        
        cv2.putText(side_view, "SIDE VIEW (X-Z)", (10, 30), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        
        side_display = cv2.resize(side_view, (600, 600))
        
        # Create main display
        display = np.zeros((vis_height, vis_width, 3), dtype=np.uint8)
        
        # Place radar view (top-left)
        display[0:600, 0:600] = radar_display
        
        # Place side view (top-right)
        display[0:600, 600:1200] = side_display
        
        # Place current camera view (bottom)
        camera_view = cv2.resize(color_image, (600, 300))
        depth_colormap = cv2.applyColorMap(
            cv2.convertScaleAbs(depth_image, alpha=0.03),
            cv2.COLORMAP_JET
        )
        depth_display = cv2.resize(depth_colormap, (600, 300))
        
        # Combine camera views
        camera_combined = np.hstack([camera_view, depth_display])
        display[600:900, 0:1200] = cv2.resize(camera_combined, (1200, 300))
        
        # Add info panel
        info_panel = np.zeros((300, 1200, 3), dtype=np.uint8)
        cv2.putText(info_panel, f"Frame: {frame_count} | Points: {len(world_points)} | Grid: {np.sum(occupancy_grid > 0)} cells", 
                   (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
        cv2.putText(info_panel, "Controls: 'q'=quit, 'c'=clear, 's'=save", 
                   (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
        cv2.putText(info_panel, f"Camera: X={camera_x:.2f}m Y={camera_y:.2f}m Z={camera_z:.2f}m", 
                   (10, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
        cv2.putText(info_panel, f"Resolution: {grid_resolution*100:.1f}cm/pixel | Max Range: {max_range:.1f}m", 
                   (10, 120), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
        
        display[900:1200, 0:1200] = info_panel
        
        cv2.imshow("3D Radar Mapper", display)
        
        frame_count += 1
        
        # Simple camera movement tracking (very basic - just for demo)
        # In real SLAM, you'd use visual odometry or IMU
        if frame_count % 30 == 0:
            # Estimate movement from point cloud (simplified)
            if len(world_vertices) > 100:
                mean_point = np.mean(world_vertices, axis=0)
                camera_x = mean_point[0] * 0.1  # Damped update
                camera_y = mean_point[1] * 0.1
                camera_z = mean_point[2] * 0.1
        
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            break
        elif key == ord('c'):
            # Clear map
            world_points.clear()
            point_colors.clear()
            occupancy_grid.fill(0)
            grid_confidence.fill(0)
            print("Map cleared!")
        elif key == ord('s'):
            # Save point cloud
            if len(world_points) > 0:
                filename = f"radar_map_{int(time.time())}.npz"
                points_array = np.array(list(world_points))
                np.savez(filename, points=points_array, occupancy_grid=occupancy_grid)
                print(f"Saved map to {filename} ({len(world_points)} points)")

except KeyboardInterrupt:
    print("\nStopped by user")
finally:
    pipeline.stop()
    cv2.destroyAllWindows()
    print("Radar mapper stopped")
