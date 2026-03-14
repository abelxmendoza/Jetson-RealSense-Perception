# Jetson-RealSense-Perception

## Project Identity

**Jetson-RealSense-Perception** is a Jetson Orin Nano embedded robotics perception sandbox running on an Intel RealSense D455 RGB-D camera. It is built for hands-on development, real-time evaluation, and portfolio-ready demos for autonomy/research systems in real-world robotics contexts.

- Host: NVIDIA Jetson Orin Nano (primary runtime)
- Camera: Intel RealSense D455
- OS: Ubuntu (Jetson JetPack), with `python3`, `pyrealsense2`, `numpy`, `opencv-python`
- Workspace: `/home/omega/Desktop/Jetson-RealSense-Perception`

## Goals

- Reliable Jetson-based depth + rgb video capture
- Obstacle detection and safe zone monitoring
- Point cloud scanning and offline visualization
- IMU data ingestion and sensor fusion readiness
- 3D mapping / occupancy-grid radar-style prototyping
- Easy SSH + remote dev workflow by ethernet

## Hardware Used

- NVIDIA Jetson Orin Nano
- Intel RealSense D455 RGB-D depth camera
- Monitor attached to Jetson for OpenCV windows
- Wired ethernet between laptop and Jetson (192.168.50.1 <-> 192.168.50.2)

## Software Stack

- Python 3 (system default on Jetson)
- pyrealsense2
- numpy
- opencv-python
- open3d (for `view_scan.py` only)

## Repository Structure

- `realsense_view.py` - basic RGB-D camera stream and center depth overlay
- `obstacle_detector.py` - navigation zone obstacle warning and visual indicator
- `point_cloud_capture.py` - capture and save point cloud data to `scan.npz`
- `view_scan.py` - open3d visualization of saved point cloud scans
- `simple_tracking.py` - ORB feature tracking / visual flow diagnostics
- `imu_stream.py` - RealSense accelerometer and gyroscope stream + graphs
- `radar_mapper.py` - occupancy-grid radar mapping prototype
- `README.md`, `Jetson-RealSense-PerceptionProject.png`, `.gitignore`

## Usage (Jetson runtime)

### 1. Start with camera validation

```bash
cd /home/omega/Desktop/Jetson-RealSense-Perception
python3 realsense_view.py
```

### 2. Run obstacle detection

```bash
python3 obstacle_detector.py
```

### 3. Capture 3D scans

```bash
python3 point_cloud_capture.py
# Press 's' to save scan.npz; 'q' to quit
```

### 4. View scans

```bash
pip3 install open3d
python3 view_scan.py [scan.npz]
```

### 5. IMU streaming

```bash
python3 imu_stream.py
```

### 6. Radar mapper

```bash
python3 radar_mapper.py
```

## GUI over SSH

When running on Jetson from laptop SSH session, use:

```bash
DISPLAY=:0 XAUTHORITY=/home/omega/.Xauthority python3 <script>.py
```

This ensures UI windows render on Jetson-connected monitor.

## Networking / Dev Workflow

- Jetson IP: `192.168.50.2` on `eno1`
- Laptop IP: `192.168.50.1`
- Check link and state:

```bash
sudo nmcli connection up eno1
sudo nmcli connection modify eno1 connection.autoconnect yes
ping 192.168.50.1
```

## Known Issues / Limitations

- RealSense D455 close range (<0.5m) is less stable; avoid over-reliance with short object distance unless re-calibrated.
- `radar_mapper.py` is heavy; may require Jetson memory budget monitoring and careful runtime.
- Do not commit `scan.npz`; `.gitignore` includes `*.npz`.
- Power stability: verify firm barrel jack seating after hard resets.

## Future Work

- Add optional ROS2 node wrappers for key modules
- Add recording-mode command-line arguments via `argparse` for each script
- Add `systemd` service wrapper for startup reprovisioning and auto-restart
- Add MQTT or HTTP telemetry output for remote monitoring
- Add data logging (timestamps + CSV) for regression tests

## Demo / Screenshots

- `Jetson-RealSense-PerceptionProject.png`: project card artwork
- capture screenshot and paste here from Jetson monitor

## Contribution and Branching

1. Keep mastable branch lean, from actual tested Jetson behavior
2. Open PRs for feature enhancements with runtime evidence / logs
3. Preserve existing pipeline stop/cleanup patterns

## Checklist before committing

- [x] `pyrealsense2`, `opencv-python`, `numpy` installed
- [x] `.gitignore` has `__pycache__/`, `*.pyc`, `*.npz`
- [x] script works with `DISPLAY`/`XAUTHORITY` on remote shell

