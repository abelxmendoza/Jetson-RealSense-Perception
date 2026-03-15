# ROS2 Integration

This folder holds notes and examples for using the RealSense camera with ROS2 Humble on the Jetson.

## Launch

The camera node is launched with the official RealSense ROS2 package:

```bash
source /opt/ros/humble/setup.bash
source ~/ros2_ws/install/setup.bash
ros2 launch realsense2_camera rs_launch.py
```

Default namespace: `/camera/camera/`. See [launch/](launch/) for parameter and custom launch notes.

## Scripts in This Repo

- **scripts/launch_realsense_ros.sh** — convenience launcher (sources ROS2 and optional workspace).
- **scripts/ros_topic_sanity.sh** — quick check that camera topics and camera_info are available.
- **scripts/save_ros_frames.py** — save one color and one depth frame from ROS topics (headless).
- **src/ros2_tools/topic_monitor.py** — list camera topics and optionally report hz.
- **src/ros2_tools/frame_info_monitor.py** — echo one camera_info from color and depth.

See main [README.md](../README.md) and [docs/validation.md](../docs/validation.md) for full validation steps.
