import pyrealsense2 as rs
import numpy as np
import cv2

pipeline = rs.pipeline()
config = rs.config()

# Lower FPS helps Jetson performance
config.enable_stream(rs.stream.color, 640, 480, rs.format.bgr8, 15)
config.enable_stream(rs.stream.depth, 640, 480, rs.format.z16, 15)

pipeline.start(config)

# Get depth scale
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

        # Distance at center pixel
        h, w = depth_image.shape
        center_x = int(w / 2)
        center_y = int(h / 2)

        distance = depth_frame.get_distance(center_x, center_y)

        cv2.putText(
            color_image,
            f"{distance:.2f} m",
            (center_x - 40, center_y - 10),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (0,255,0),
            2
        )

        cv2.circle(color_image,(center_x,center_y),5,(0,255,0),-1)

        depth_colormap = cv2.applyColorMap(
            cv2.convertScaleAbs(depth_image, alpha=0.04),
            cv2.COLORMAP_JET
        )

        combined = np.hstack((color_image, depth_colormap))

        cv2.imshow("RealSense RGB-D", combined)

        if cv2.waitKey(1) == 27:
            break

finally:
    pipeline.stop()
    cv2.destroyAllWindows()
