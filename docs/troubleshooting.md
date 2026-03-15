# Troubleshooting

Common issues encountered on Jetson + RealSense + ROS2 and how to resolve them.

## Wrong rs-enumerate-devices Binary

- **Symptom:** Validation or version checks don’t match your built librealsense.
- **Cause:** An older binary is first in `PATH` (e.g. from ROS: `/opt/ros/humble/bin/rs-enumerate-devices`).
- **Fix:** Call the SDK binary explicitly: `/usr/local/bin/rs-enumerate-devices`. Prefer this when validating the source build.

## "bad optional access" or Similar C++ Errors

- **Symptom:** Crash or exception when starting the RealSense ROS node or SDK tools.
- **Cause:** Version mismatch between the realsense-ros wrapper and the installed librealsense (API/ABI mismatch).
- **Fix:** Use a realsense-ros branch/tag that matches your librealsense version; rebuild realsense-ros and the workspace.

## Headless: No Display / Qt / GUI Errors

- **Symptom:** `cv2.imshow()` fails, or rqt/rqt_image_view fails with display or Qt errors.
- **Cause:** No display server (e.g. SSH session, TTY, or DISPLAY not set).
- **Fix:** Run headless-friendly scripts: use `scripts/capture_color_depth.py` to save images, or `ros2 topic echo` / `scripts/save_ros_frames.py` for ROS. For standalone scripts that support it, use `--no-gui` (e.g. `imu_stream.py --no-gui`).

## "No device connected" While ROS Node Is Running

- **Symptom:** Standalone pyrealsense2 script reports no device or fails to open.
- **Cause:** The RealSense device is already opened by the ROS2 realsense2_camera node.
- **Fix:** Stop the ROS2 node (Ctrl+C), then run the standalone script. Only one process can use the camera at a time.

## Missing ROS Dependencies (e.g. diagnostic_updater)

- **Symptom:** realsense-ros fails to build with missing package errors.
- **Fix:** Install the reported packages (e.g. `sudo apt install ros-humble-diagnostic-updater`) and run `rosdep install --from-paths src --ignore-src -r -y` in the workspace.

## Topic Exists but GUI Viewer Fails

- **Symptom:** `ros2 topic list` shows camera topics, but rqt_image_view or similar fails.
- **Cause:** Headless environment or Qt/display issues.
- **Fix:** Validate via CLI: `ros2 topic echo /camera/camera/color/camera_info --once`, or use `scripts/save_ros_frames.py` to save frames to disk.

## Center Distance Returns 0.000 m

- **Symptom:** Center depth probe or overlay shows 0.000 m.
- **Cause:** Invalid or no depth at that pixel (e.g. no surface in range, or depth stream not aligned/valid).
- **Fix:** Point camera at a textured surface in valid range (e.g. 0.3–10 m for D455). Ensure depth stream is enabled and not blocked by another process.

## Permission / Stale Build Artifacts

- **Symptom:** Build fails or binaries behave oddly; "permission denied" or outdated behavior.
- **Fix:** Ensure build directories are not owned by root if you build as user. Clean and rebuild: `rm -rf build install log` then `colcon build`. For librealsense, do a clean rebuild and reinstall if needed.
