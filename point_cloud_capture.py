import pyrealsense2 as rs
import numpy as np
import cv2
import time

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
retry_delay = 2  # seconds

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
                print("\nTroubleshooting:")
                print("1. Wait 5-10 seconds and try again")
                print("2. Unplug and replug the camera USB cable")
                print("3. Check if another program is using the camera")
                exit(1)
        else:
            print(f"Error starting camera: {e}")
            exit(1)

# Create point cloud processor
pc = rs.pointcloud()

try:
    while True:
        frames = pipeline.wait_for_frames()
        aligned_frames = rs.align(rs.stream.color).process(frames)
        
        depth_frame = aligned_frames.get_depth_frame()
        color_frame = aligned_frames.get_color_frame()
        
        if not depth_frame or not color_frame:
            continue
        
        # Generate point cloud
        points = pc.calculate(depth_frame)
        pc.map_to(color_frame)
        
        # Get point cloud data
        vertices = np.asanyarray(points.get_vertices()).view(np.float32).reshape(-1, 3)
        colors = np.asanyarray(points.get_texture_coordinates()).view(np.float32).reshape(-1, 2)
        
        # Display preview
        color_image = np.asanyarray(color_frame.get_data())
        depth_colormap = cv2.applyColorMap(
            cv2.convertScaleAbs(np.asanyarray(depth_frame.get_data()), alpha=0.03),
            cv2.COLORMAP_JET
        )
        
        # Add instructions overlay
        display_image = color_image.copy()
        cv2.putText(display_image, "Press 's' to save point cloud, 'q' to quit", 
                   (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        cv2.putText(display_image, f"Points: {len(vertices)}", 
                   (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        
        cv2.imshow("RGB", display_image)
        cv2.imshow("Depth", depth_colormap)
        
        key = cv2.waitKey(1) & 0xFF
        if key == ord('s'):
            # Save point cloud
            np.savez('scan.npz', vertices=vertices, colors=colors, color_image=color_image)
            print(f"Saved point cloud with {len(vertices)} points to scan.npz")
            cv2.putText(display_image, "SAVED!", (10, 90), 
                       cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            cv2.imshow("RGB", display_image)
            cv2.waitKey(1000)  # Show saved message for 1 second
        elif key == ord('q'):
            break
finally:
    pipeline.stop()
    cv2.destroyAllWindows()
