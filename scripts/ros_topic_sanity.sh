#!/usr/bin/env bash
# Quick sanity check for RealSense ROS2 topics.
# Run from a terminal where you have already sourced ROS2 and your workspace, e.g.:
#   source /opt/ros/humble/setup.bash
#   source ~/ros2_ws/install/setup.bash
# Then: ./scripts/ros_topic_sanity.sh
# Or from repo root: bash scripts/ros_topic_sanity.sh

set -e

echo "=== ROS2 node list ==="
ros2 node list || true

echo ""
echo "=== Camera-related topics ==="
ros2 topic list | grep -E "camera|depth|color" || true

echo ""
echo "=== Color image topic info ==="
ros2 topic info /camera/camera/color/image_raw 2>/dev/null || echo "(topic not available)"

echo ""
echo "=== Depth image topic info ==="
ros2 topic info /camera/camera/depth/image_rect_raw 2>/dev/null || echo "(topic not available)"

echo ""
echo "=== Color camera_info (one message) ==="
timeout 3 ros2 topic echo /camera/camera/color/camera_info --once 2>/dev/null || echo "(no message received)"

echo ""
echo "=== Depth camera_info (one message) ==="
timeout 3 ros2 topic echo /camera/camera/depth/camera_info --once 2>/dev/null || echo "(no message received)"

echo ""
echo "Done. If topics are missing, start the RealSense node first: ros2 launch realsense2_camera rs_launch.py"
