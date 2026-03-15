# Architecture

This repository implements a reproducible Jetson + RealSense ROS2 perception stack.

Goals:
- Hardware bring-up on Jetson Orin Nano
- RealSense D455 sensor pipeline
- ROS2 driver layer (`realsense2_camera`)
- Topic validation and structured telemetry
- Visualization in RViz and Foxglove
- Data recording via ros2 bag
- Remote debugging using foxglove_bridge

Pipeline:
1. Jetson Orin Nano + RealSense D455
2. `realsense2_camera` ROS2 driver
3. ROS2 topics for color/depth/camera_info
4. Downstream nodes for filtering, mapping, detection
5. Visualization (RViz / Foxglove)
6. Optional data capture (`ros2 bag`)
