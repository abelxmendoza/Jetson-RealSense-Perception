#!/usr/bin/env bash
# Convenience launcher for RealSense ROS2 node.
# Ensure no standalone pyrealsense2 script is using the camera before launching.
#
# Usage:
#   ./scripts/launch_realsense_ros.sh
# Or from repo root: bash scripts/launch_realsense_ros.sh
#
# If your workspace is elsewhere, source it first, then run:
#   ros2 launch realsense2_camera rs_launch.py

# Uncomment and set if your workspace is not in default location:
# source /opt/ros/humble/setup.bash
# source ~/ros2_ws/install/setup.bash

if [ -f "/opt/ros/humble/setup.bash" ]; then
    source /opt/ros/humble/setup.bash
fi
if [ -f "$HOME/ros2_ws/install/setup.bash" ]; then
    source "$HOME/ros2_ws/install/setup.bash"
fi

echo "Launching realsense2_camera (stop any pyrealsense2 scripts first)..."
exec ros2 launch realsense2_camera rs_launch.py "$@"
