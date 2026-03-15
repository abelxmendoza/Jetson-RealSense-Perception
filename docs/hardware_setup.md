# Hardware Setup

## Platform

- **Compute:** NVIDIA Jetson Orin Nano
- **OS:** Ubuntu 22.04 (JetPack / L4T 36.4.7)
- **Camera:** Intel RealSense D455 RGB-D

## D455 Connection

- Use **USB 3.x** (USB 3.2 preferred). The camera should enumerate as USB 3.2 when working correctly.
- Connect directly to the Jetson USB port; avoid unreliable hubs for perception workloads.
- Ensure the camera is firmly seated; loose connection can cause "No device connected" or enumeration failures.

## Headless vs GUI

- The Jetson may be used **headless** (SSH, no monitor). In that case there is no display server; OpenCV `imshow()` and GUI tools like `rqt_image_view` will fail.
- Validation and capture should support **headless workflows**: use CLI scripts, save images to disk, and check with `scripts/capture_color_depth.py` or ROS topic echo instead of GUI viewers.
- When a display is attached, you can run GUI-based demos (e.g. `realsense_view.py`, obstacle detector with window).

## Verification

- After connecting the camera, run `scripts/check_realsense.py` or `/usr/local/bin/rs-enumerate-devices` to confirm the D455 is detected and report its name, serial, and firmware.
