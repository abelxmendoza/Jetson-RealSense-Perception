# rs_launch.py Example

The standard launch command:

```bash
ros2 launch realsense2_camera rs_launch.py
```

## Common Parameters

Pass parameters with `:=` (example):

```bash
ros2 launch realsense2_camera rs_launch.py \
  depth_module.depth_profile:=640x480x30 \
  rgb_camera.color_profile:=640x480x30
```

- **Point cloud:** `pointcloud.enable:=true`
- **Align depth to color:** `align_depth.enable:=true`
- **Disable color:** `enable_color:=false` (depth-only)

See the [realsense-ros](https://github.com/realsenseai/realsense-ros) documentation for the full parameter list.
