# Validation Checklist

Use these commands to validate the Jetson + RealSense + ROS2 stack. Run in order when possible.

## 1. RealSense SDK (librealsense)

Prefer the binary from your source install:

```bash
which rs-enumerate-devices
/usr/local/bin/rs-enumerate-devices
```

Expected: Device listed (e.g. D455) with serial and firmware.

## 2. Python / pyrealsense2

```bash
python3 scripts/check_realsense.py
```

Expected: Exit 0, device name/serial/firmware printed.

## 3. Standalone Stream Test (Optional GUI)

If you have a display:

```bash
python3 src/standalone/realsense_view.py
```

Or headless capture:

```bash
python3 scripts/capture_color_depth.py -o assets/sample_outputs
```

Expected: `color.png` and `depth.png` written; no device errors.

## 4. ROS2 Launch

In one terminal (source ROS2 and workspace first):

```bash
source /opt/ros/humble/setup.bash
source ~/ros2_ws/install/setup.bash
ros2 launch realsense2_camera rs_launch.py
```

Expected: Node starts without "No device connected" or crash.

## 5. ROS2 Node and Topics

In another terminal (with the same sourcing):

```bash
ros2 node list
ros2 topic list | grep camera
```

Expected: RealSense node visible; topics such as `/camera/camera/color/image_raw`, `/camera/camera/depth/image_rect_raw`, etc.

## 6. Camera Info (Intrinsics)

```bash
ros2 topic echo /camera/camera/color/camera_info --once
ros2 topic echo /camera/camera/depth/camera_info --once
```

Expected: One message each with valid `K` (intrinsic matrix) and dimensions.

## 7. Topic Rate

```bash
ros2 topic hz /camera/camera/color/image_raw
ros2 topic hz /camera/camera/depth/image_rect_raw
```

Expected: Stable rate (e.g. 30 Hz depending on config). Ctrl+C to stop.

## 8. Sanity Script

```bash
bash scripts/ros_topic_sanity.sh
```

Expected: Node list, camera topics, and one-shot camera_info samples (if node is running).

## 9. Save Frames from ROS (Headless)

With the RealSense ROS node running:

```bash
python3 scripts/save_ros_frames.py -o assets/sample_outputs
```

Expected: `ros_color.png` and `ros_depth.png` in the output directory.

---

If any step fails, see [troubleshooting.md](troubleshooting.md) and [software_setup.md](software_setup.md).
