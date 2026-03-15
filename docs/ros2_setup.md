# ROS2 Setup

## Workspace and realsense-ros

1. Create a ROS2 workspace (e.g. `~/ros2_ws`).
2. Clone the RealSense ROS2 wrapper into the workspace src:
   - **Repository:** https://github.com/realsenseai/realsense-ros  
   - RealSense repos have moved to the [RealSenseAI](https://github.com/realsenseai) organization.
3. Install dependencies (e.g. `rosdep install --from-paths src --ignore-src -r -y`). Resolve any missing packages (e.g. `diagnostic_updater`).
4. **Version matching:** Use a branch/tag of realsense-ros that is compatible with your installed (or built) librealsense version. Version mismatch can cause build or runtime errors (e.g. "bad optional access" or API mismatches).
5. Build the workspace: `colcon build --symlink-install` (or equivalent).
6. Source the workspace: `source ~/ros2_ws/install/setup.bash`.

## Launching the Camera Node

After sourcing ROS2 and the workspace:

```bash
source /opt/ros/humble/setup.bash
source ~/ros2_ws/install/setup.bash
ros2 launch realsense2_camera rs_launch.py
```

Default topic namespace is `/camera/camera/`. Confirmed working topics in this setup:

- `/camera/camera/color/image_raw`
- `/camera/camera/depth/image_rect_raw`
- `/camera/camera/color/camera_info`
- `/camera/camera/depth/camera_info`

Camera info and intrinsics publish correctly once the node is running.

## Notes

- Only one process can own the RealSense device at a time. If the ROS2 node is running, standalone `pyrealsense2` scripts cannot open the camera (and vice versa).
- For custom launch parameters (resolution, FPS, filters), see the [realsense-ros](https://github.com/realsenseai/realsense-ros) documentation and `ros2/launch/` notes in this repo.
