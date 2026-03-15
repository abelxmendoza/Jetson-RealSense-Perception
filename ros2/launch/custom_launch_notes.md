# Custom Launch Notes

- Use a **realsense-ros** version compatible with your installed librealsense to avoid build/runtime errors.
- If you create a custom launch file, place it in your ROS2 workspace and launch it with `ros2 launch <pkg> <launch_file>.py`.
- Camera namespace and name can be set via parameters (e.g. `camera_namespace`, `camera_name`) so multiple robots/cameras can be distinguished.
