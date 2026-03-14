"""
Stream and visualize IMU data (accelerometer and gyroscope) from RealSense camera.
"""
import pyrealsense2 as rs
import numpy as np
import cv2
import time

# Try to release any existing pipeline connections
ctx = rs.context()
devices = ctx.query_devices()
if len(devices) > 0:
    device = devices[0]
    print(f"Found RealSense device: {device.get_info(rs.camera_info.name)}")
    
    # Check if IMU is available
    sensors = device.query_sensors()
    has_imu = False
    for sensor in sensors:
        sensor_name = sensor.get_info(rs.camera_info.name)
        if 'Motion' in sensor_name:
            has_imu = True
            print(f"Found IMU sensor: {sensor_name}")
            break
    
    if not has_imu:
        print("Warning: IMU may not be available on this device")
        print("This script works with D435i, D455, and other models with IMU")

pipeline = rs.pipeline()
config = rs.config()

# Enable IMU streams - find available frame rates first
try:
    # Find available IMU profiles
    device = devices[0]
    sensors = device.query_sensors()
    accel_fps = None
    gyro_fps = None
    
    for sensor in sensors:
        if 'Motion' in sensor.get_info(rs.camera_info.name):
            profiles = sensor.get_stream_profiles()
            for profile in profiles:
                if profile.stream_type() == rs.stream.accel and accel_fps is None:
                    accel_fps = profile.fps()
                    print(f"Found accelerometer: {accel_fps} Hz")
                elif profile.stream_type() == rs.stream.gyro and gyro_fps is None:
                    gyro_fps = profile.fps()
                    print(f"Found gyroscope: {gyro_fps} Hz")
    
    # Use found frame rates, or defaults
    if accel_fps is None:
        accel_fps = 200  # Default
        print(f"Using default accelerometer rate: {accel_fps} Hz")
    if gyro_fps is None:
        gyro_fps = 200  # Default
        print(f"Using default gyroscope rate: {gyro_fps} Hz")
    
    config.enable_stream(rs.stream.accel, rs.format.motion_xyz32f, accel_fps)
    config.enable_stream(rs.stream.gyro, rs.format.motion_xyz32f, gyro_fps)
    print(f"Configured IMU streams: Accel @ {accel_fps}Hz, Gyro @ {gyro_fps}Hz")
except Exception as e:
    print(f"Error enabling IMU streams: {e}")
    print("Your device may not support IMU, or streams may need different configuration")
    exit(1)

# Try to start pipeline with retry logic
max_retries = 3
retry_delay = 2  # seconds

for attempt in range(max_retries):
    try:
        profile = pipeline.start(config)
        print("IMU streams started successfully!")
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
                exit(1)
        else:
            print(f"Error starting camera: {e}")
            exit(1)

# Data storage for visualization
accel_history = []
gyro_history = []
max_history = 200  # Keep last 200 samples

try:
    print("\nStreaming IMU data...")
    print("Press 'q' to quit, 's' to save data to file")
    
    start_time = time.time()
    frame_count = 0
    
    while True:
        frames = pipeline.wait_for_frames()
        
        # Get IMU frames
        accel_frame = frames.first_or_default(rs.stream.accel)
        gyro_frame = frames.first_or_default(rs.stream.gyro)
        
        current_time = time.time() - start_time
        
        # Process accelerometer data
        if accel_frame:
            accel_data = accel_frame.as_motion_frame().get_motion_data()
            accel_vec = np.array([accel_data.x, accel_data.y, accel_data.z])
            accel_history.append((current_time, accel_vec.copy()))
            if len(accel_history) > max_history:
                accel_history.pop(0)
            
            # Calculate magnitude (useful for detecting motion)
            accel_magnitude = np.linalg.norm(accel_vec)
            
            # Calculate pitch and roll from accelerometer (simple tilt estimation)
            pitch = np.arctan2(accel_data.x, np.sqrt(accel_data.y**2 + accel_data.z**2)) * 180 / np.pi
            roll = np.arctan2(accel_data.y, accel_data.z) * 180 / np.pi
        
        # Process gyroscope data
        if gyro_frame:
            gyro_data = gyro_frame.as_motion_frame().get_motion_data()
            gyro_vec = np.array([gyro_data.x, gyro_data.y, gyro_data.z])
            gyro_history.append((current_time, gyro_vec.copy()))
            if len(gyro_history) > max_history:
                gyro_history.pop(0)
            
            # Calculate angular velocity magnitude
            gyro_magnitude = np.linalg.norm(gyro_vec)
        
        frame_count += 1
        
        # Print data every 50 frames (to avoid spam)
        if frame_count % 50 == 0:
            if accel_frame:
                print(f"Time: {current_time:.2f}s | "
                      f"Accel: [{accel_data.x:7.3f}, {accel_data.y:7.3f}, {accel_data.z:7.3f}] m/s² | "
                      f"Mag: {accel_magnitude:.3f} | "
                      f"Pitch: {pitch:6.1f}° Roll: {roll:6.1f}°")
            if gyro_frame:
                print(f"Time: {current_time:.2f}s | "
                      f"Gyro:  [{gyro_data.x:7.3f}, {gyro_data.y:7.3f}, {gyro_data.z:7.3f}] rad/s | "
                      f"Mag: {gyro_magnitude:.3f}")
        
        # Create visualization
        vis_width, vis_height = 800, 600
        vis_image = np.zeros((vis_height, vis_width, 3), dtype=np.uint8)
        
        # Draw accelerometer graph
        if len(accel_history) > 1:
            cv2.putText(vis_image, "Accelerometer (m/s^2)", (10, 20), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
            
            # Draw axes
            center_y = 150
            graph_width = 750
            graph_height = 100
            
            # X axis (red)
            for i in range(1, len(accel_history)):
                t1, a1 = accel_history[i-1]
                t2, a2 = accel_history[i]
                x1 = int((t1 - accel_history[0][0]) / (accel_history[-1][0] - accel_history[0][0] + 0.001) * graph_width)
                x2 = int((t2 - accel_history[0][0]) / (accel_history[-1][0] - accel_history[0][0] + 0.001) * graph_width)
                y1 = int(center_y - a1[0] * 20)  # Scale factor
                y2 = int(center_y - a2[0] * 20)
                cv2.line(vis_image, (x1, y1), (x2, y2), (0, 0, 255), 2)
            
            # Y axis (green)
            for i in range(1, len(accel_history)):
                t1, a1 = accel_history[i-1]
                t2, a2 = accel_history[i]
                x1 = int((t1 - accel_history[0][0]) / (accel_history[-1][0] - accel_history[0][0] + 0.001) * graph_width)
                x2 = int((t2 - accel_history[0][0]) / (accel_history[-1][0] - accel_history[0][0] + 0.001) * graph_width)
                y1 = int(center_y - a1[1] * 20)
                y2 = int(center_y - a2[1] * 20)
                cv2.line(vis_image, (x1, y1), (x2, y2), (0, 255, 0), 2)
            
            # Z axis (blue)
            for i in range(1, len(accel_history)):
                t1, a1 = accel_history[i-1]
                t2, a2 = accel_history[i]
                x1 = int((t1 - accel_history[0][0]) / (accel_history[-1][0] - accel_history[0][0] + 0.001) * graph_width)
                x2 = int((t2 - accel_history[0][0]) / (accel_history[-1][0] - accel_history[0][0] + 0.001) * graph_width)
                y1 = int(center_y - a1[2] * 20)
                y2 = int(center_y - a2[2] * 20)
                cv2.line(vis_image, (x1, y1), (x2, y2), (255, 0, 0), 2)
            
            # Zero line
            cv2.line(vis_image, (0, center_y), (graph_width, center_y), (128, 128, 128), 1)
        
        # Draw gyroscope graph
        if len(gyro_history) > 1:
            cv2.putText(vis_image, "Gyroscope (rad/s)", (10, 300), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
            
            center_y = 430
            graph_width = 750
            graph_height = 100
            
            # X axis (red)
            for i in range(1, len(gyro_history)):
                t1, g1 = gyro_history[i-1]
                t2, g2 = gyro_history[i]
                x1 = int((t1 - gyro_history[0][0]) / (gyro_history[-1][0] - gyro_history[0][0] + 0.001) * graph_width)
                x2 = int((t2 - gyro_history[0][0]) / (gyro_history[-1][0] - gyro_history[0][0] + 0.001) * graph_width)
                y1 = int(center_y - g1[0] * 50)  # Scale factor for rad/s
                y2 = int(center_y - g2[0] * 50)
                cv2.line(vis_image, (x1, y1), (x2, y2), (0, 0, 255), 2)
            
            # Y axis (green)
            for i in range(1, len(gyro_history)):
                t1, g1 = gyro_history[i-1]
                t2, g2 = gyro_history[i]
                x1 = int((t1 - gyro_history[0][0]) / (gyro_history[-1][0] - gyro_history[0][0] + 0.001) * graph_width)
                x2 = int((t2 - gyro_history[0][0]) / (gyro_history[-1][0] - gyro_history[0][0] + 0.001) * graph_width)
                y1 = int(center_y - g1[1] * 50)
                y2 = int(center_y - g2[1] * 50)
                cv2.line(vis_image, (x1, y1), (x2, y2), (0, 255, 0), 2)
            
            # Z axis (blue)
            for i in range(1, len(gyro_history)):
                t1, g1 = gyro_history[i-1]
                t2, g2 = gyro_history[i]
                x1 = int((t1 - gyro_history[0][0]) / (gyro_history[-1][0] - gyro_history[0][0] + 0.001) * graph_width)
                x2 = int((t2 - gyro_history[0][0]) / (gyro_history[-1][0] - gyro_history[0][0] + 0.001) * graph_width)
                y1 = int(center_y - g1[2] * 50)
                y2 = int(center_y - g2[2] * 50)
                cv2.line(vis_image, (x1, y1), (x2, y2), (255, 0, 0), 2)
            
            # Zero line
            cv2.line(vis_image, (0, center_y), (graph_width, center_y), (128, 128, 128), 1)
        
        # Display current values
        if accel_frame:
            cv2.putText(vis_image, f"Accel X: {accel_data.x:6.3f} Y: {accel_data.y:6.3f} Z: {accel_data.z:6.3f}", 
                       (10, 550), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
            cv2.putText(vis_image, f"Pitch: {pitch:5.1f}deg  Roll: {roll:5.1f}deg  Mag: {accel_magnitude:.3f}", 
                       (10, 570), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        
        if gyro_frame:
            cv2.putText(vis_image, f"Gyro  X: {gyro_data.x:6.3f} Y: {gyro_data.y:6.3f} Z: {gyro_data.z:6.3f}", 
                       (10, 590), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        
        cv2.imshow("IMU Data Stream", vis_image)
        
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            break
        elif key == ord('s'):
            # Save data to file
            filename = f"imu_data_{int(time.time())}.npz"
            np.savez(filename, 
                    accel_history=np.array([(t, a[0], a[1], a[2]) for t, a in accel_history]),
                    gyro_history=np.array([(t, g[0], g[1], g[2]) for t, g in gyro_history]))
            print(f"\nSaved IMU data to {filename}")
            cv2.putText(vis_image, "SAVED!", (300, 300), 
                       cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            cv2.imshow("IMU Data Stream", vis_image)
            cv2.waitKey(1000)

except KeyboardInterrupt:
    print("\nStopped by user")
finally:
    pipeline.stop()
    cv2.destroyAllWindows()
    print("IMU streaming stopped")
