# Software Setup

## Proven Stack

- **Ubuntu:** 22.04 on Jetson Orin Nano (L4T 36.4.7)
- **ROS2:** Humble
- **RealSense SDK:** librealsense built from source with **RSUSB backend**

## librealsense from Source

- The native Jetson L4T patch script from Intel/RealSense was **not** used in this setup due to unsupported JetPack revision in the environment.
- The working path was building **librealsense from source with the RSUSB backend** (no kernel patches). Follow the official [librealsense installation](https://github.com/realsenseai/librealsense) and, for Jetson, the [installation_jetson](https://github.com/realsenseai/librealsense/blob/master/doc/installation_jetson.md) notes where applicable; use RSUSB if kernel patches are not an option.
- After building, install so that **pyrealsense2** is available (Python bindings are built with the SDK).
- Prefer **`/usr/local/bin/rs-enumerate-devices`** when validating the local source build. The ROS-installed or system package may install an older binary under `/opt/ros/humble/bin` or elsewhere; using `/usr/local/bin/rs-enumerate-devices` ensures you are testing the SDK you built.

## Python Stack

- **Python 3**
- **pyrealsense2** — from the librealsense build (not pip for the SDK itself)
- **numpy** (&lt; 2.0 for compatibility), **opencv-python** — `pip3 install numpy opencv-python`
- **open3d** (optional) — for `view_scan.py`: `pip3 install open3d`

## ROS2

- Install ROS2 Humble and the RealSense ROS2 wrapper (realsense-ros). See [ros2_setup.md](ros2_setup.md).
