import pyrealsense2 as rs
import numpy as np
import cv2

pipeline = rs.pipeline()
config = rs.config()

# Lower FPS helps a lot on Jetson
config.enable_stream(rs.stream.color, 640, 480, rs.format.bgr8, 15)
config.enable_stream(rs.stream.depth, 640, 480, rs.format.z16, 15)

pipeline.start(config)

# Depth scale for real distance
depth_sensor = pipeline.get_active_profile().get_device().first_depth_sensor()
depth_scale = depth_sensor.get_depth_scale()

print("Depth Scale:", depth_scale)

try:
    while True:

        frames = pipeline.wait_for_frames()

        depth_frame = frames.get_depth_frame()
        color_frame = frames.get_color_frame()

        if not depth_frame or not color_frame:
            continue

        depth_image = np.asanyarray(depth_frame.get_data())
        color_image = np.asanyarray(color_frame.get_data())

        # Normalize depth image
        depth_colormap = cv2.applyColorMap(
            cv2.convertScaleAbs(depth_image, alpha=0.04),
            cv2.COLORMAP_JET
        )

        # Stack images for single window (faster than 2 windows)
        combined = np.hstack((color_image, depth_colormap))

        cv2.imshow("RealSense RGB + Depth", combined)

        if cv2.waitKey(1) == 27:  # ESC key
            break

finally:
    pipeline.stop()
    cv2.destroyAllWindows()