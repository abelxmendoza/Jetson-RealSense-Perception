import pyrealsense2 as rs
import numpy as np
import cv2
import time

# Feature detector for tracking
orb = cv2.ORB_create()

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
                # Try to stop any existing pipeline
                try:
                    pipeline.stop()
                except:
                    pass
                pipeline = rs.pipeline()  # Create new pipeline instance
            else:
                print(f"Error starting camera: {e}")
                print("\nTroubleshooting:")
                print("1. Wait 5-10 seconds and try again")
                print("2. Unplug and replug the camera USB cable")
                print("3. Check if another program is using the camera")
                print("4. Try running: sudo fuser -k /dev/video*")
                exit(1)
        else:
            print(f"Error starting camera: {e}")
            exit(1)

prev_frame = None
prev_kp = None
prev_desc = None
position = np.array([0.0, 0.0, 0.0])  # Simple position tracker
frame_count = 0

try:
    while True:
        frames = pipeline.wait_for_frames()
        color_frame = frames.get_color_frame()
        
        if not color_frame:
            continue
        
        color_image = np.asanyarray(color_frame.get_data())
        gray = cv2.cvtColor(color_image, cv2.COLOR_BGR2GRAY)
        
        # Detect features
        kp, desc = orb.detectAndCompute(gray, None)
        
        # Draw current features
        frame_with_features = color_image.copy()
        if kp:
            cv2.drawKeypoints(frame_with_features, kp, frame_with_features, 
                            flags=cv2.DRAW_MATCHES_FLAGS_DRAW_RICH_KEYPOINTS)
        
        if prev_kp is not None and desc is not None and prev_desc is not None:
            # Match features
            bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)
            matches = bf.match(prev_desc, desc)
            matches = sorted(matches, key=lambda x: x.distance)
            
            # Draw matches
            if len(matches) > 0:
                img_matches = cv2.drawMatches(prev_frame, prev_kp, gray, kp, 
                                            matches[:30], None, 
                                            flags=cv2.DrawMatchesFlags_NOT_DRAW_SINGLE_POINTS)
                cv2.imshow("Feature Tracking", img_matches)
                
                # Simple movement estimate (very basic)
                if len(matches) > 10:
                    match_quality = len(matches) / max(len(prev_kp), len(kp))
                    print(f"Frame {frame_count}: Tracking {len(matches)} features | "
                          f"Match quality: {match_quality:.2f} | Position: {position}")
            else:
                cv2.imshow("Feature Tracking", frame_with_features)
        else:
            cv2.imshow("Feature Tracking", frame_with_features)
        
        prev_frame = gray.copy()
        prev_kp = kp
        prev_desc = desc
        frame_count += 1
        
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
finally:
    pipeline.stop()
    cv2.destroyAllWindows()
