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

try:
    while True:
        frames = pipeline.wait_for_frames()
        depth_frame = frames.get_depth_frame()
        color_frame = frames.get_color_frame()
        
        if not depth_frame or not color_frame:
            continue
        
        depth_image = np.asanyarray(depth_frame.get_data())
        color_image = np.asanyarray(color_frame.get_data())
        
        # Get center region depth (navigation zone)
        h, w = depth_image.shape
        center_region = depth_image[h//3:2*h//3, w//3:2*w//3]
        valid_depths = center_region[center_region > 0]
        
        if len(valid_depths) > 0:
            min_distance = np.min(valid_depths) / 1000.0  # Convert to meters
        else:
            min_distance = 10.0  # Default if no valid depth
        
        # Draw warning overlay
        overlay = color_image.copy()
        if min_distance < 0.5:
            cv2.rectangle(overlay, (w//3, h//3), (2*w//3, 2*h//3), (0, 0, 255), 3)
            text = f"OBSTACLE: {min_distance:.2f}m"
            cv2.putText(overlay, text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
        else:
            text = f"Clear: {min_distance:.2f}m"
            cv2.putText(overlay, text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        
        # Draw navigation zone indicator
        cv2.rectangle(overlay, (w//3, h//3), (2*w//3, 2*h//3), (255, 255, 0), 1)
        
        cv2.imshow("Navigation View", overlay)
        
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
finally:
    pipeline.stop()
    cv2.destroyAllWindows()
