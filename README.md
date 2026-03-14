# Jetson RealSense Perception Toolkit

<p align="center">
  <img src="./Jetson-RealSense-PerceptionProject.png" alt="Jetson RealSense Perception Project" width="800"/>
</p>

**Embedded RGB-D perception system for robotics using Jetson Orin Nano and Intel RealSense cameras.**

---

## Table of contents

- [Overview](#overview)
- [Hardware](#hardware)
- [System architecture](#system-architecture)
- [Scripts](#scripts)
- [Getting started](#getting-started)
- [Requirements](#requirements)
- [Tips](#tips)
- [Future work](#future-work)
- [License](#license)

---

## Overview

This toolkit provides **perception pipelines** for autonomous robots and drones: RGB-D sensing, obstacle detection, 3D mapping, feature tracking, and IMU streaming. All modules run on the **Jetson Orin Nano** with an **Intel RealSense D455**, from camera to OpenCV/NumPy processing on the embedded system.

| Capability            | Script                  |
|-----------------------|-------------------------|
| RGB + depth viewing   | `realsense_view.py`     |
| Obstacle detection    | `obstacle_detector.py`  |
| 3D point cloud capture| `point_cloud_capture.py`|
| Point cloud viewer    | `view_scan.py`          |
| Feature tracking      | `simple_tracking.py`    |
| IMU streaming         | `imu_stream.py`         |
| Live occupancy map    | `radar_mapper.py`       |

---

## Hardware

| Component | Model |
|-----------|--------|
| Compute  | NVIDIA Jetson Orin Nano |
| Camera   | Intel RealSense D455 RGB-D |

---

## System architecture

Pipeline: **sensor → SDK → bindings → your logic → embedded system.** Getting this running on an embedded GPU is a system-integration task.

```
Intel RealSense D455
        ↓
librealsense SDK
        ↓
pyrealsense2
        ↓
Python perception modules
        ↓
OpenCV / NumPy processing
        ↓
Jetson Orin Nano (embedded system)
```

---

## Scripts

### 1. `realsense_view.py` — Basic viewer

RGB and depth stream viewer. Use this first to confirm the camera works.

```bash
python3 realsense_view.py
```

**Controls:** `q` — quit

---

### 2. `obstacle_detector.py` — Navigation helper

Monitors a central navigation zone and warns when obstacles are too close.

```bash
python3 obstacle_detector.py
```

| Indicator | Meaning |
|-----------|---------|
| Yellow rectangle | Monitored zone |
| Green text | Clear path |
| Red text | Obstacle &lt; 0.5 m |

**Controls:** `q` — quit

---

### 3. `point_cloud_capture.py` — 3D scanning

Capture and save 3D point clouds for later use.

```bash
python3 point_cloud_capture.py
```

**Controls:** `s` — save frame as point cloud · `q` — quit  
**Output:** `scan.npz`

---

### 4. `view_scan.py` — Point cloud viewer

Visualize saved `.npz` point cloud scans in 3D.

```bash
pip3 install open3d   # required
python3 view_scan.py [scan_file.npz]
```

Defaults to `scan.npz` if no file is given.

---

### 5. `simple_tracking.py` — Feature tracking

Visual feature tracking between frames (motion-from-features style).

```bash
python3 simple_tracking.py
```

Shows feature matches and prints tracking stats. **Controls:** `q` — quit

---

### 6. `imu_stream.py` — IMU streaming

Stream and plot accelerometer and gyroscope data from the camera IMU.

```bash
python3 imu_stream.py
```

- Real-time plots: accel (X,Y,Z), gyro (X,Y,Z)  
- Pitch/roll from accel, motion magnitude  
- **Controls:** `s` — save data · `q` — quit  

**Note:** Needs a RealSense with IMU (e.g. D435i, D455).

---

### 7. `radar_mapper.py` — 3D radar mapper

Live occupancy grid with radar-style top-down view. Builds a map as you move the camera.

```bash
python3 radar_mapper.py
```

- Top-down radar view, side view (X–Z), live RGB/depth  
- 2 cm resolution occupancy grid, confidence-based coloring  
- **Controls:** `c` — clear map · `s` — save map · `q` — quit  

---

## Getting started

1. **Check camera:** `python3 realsense_view.py`
2. **Obstacle check:** `python3 obstacle_detector.py`
3. **Capture scan:** `python3 point_cloud_capture.py` → then `python3 view_scan.py`
4. **Tracking:** `python3 simple_tracking.py`
5. **IMU (if supported):** `python3 imu_stream.py`
6. **Mapping:** `python3 radar_mapper.py`

---

## Requirements

- **Python 3**
- **Packages:** `pyrealsense2`, `numpy` (&lt;2.0), `opencv-python`
- **Optional:** `open3d` (for `view_scan.py`)

```bash
pip3 install numpy opencv-python open3d
```

Install `pyrealsense2` per [Intel RealSense documentation](https://github.com/IntelRealSense/librealsense) for your platform (Jetson has specific instructions).

---

## Tips

- Update RealSense firmware for best compatibility.
- Good lighting improves depth quality; typical range 0.3 m–10 m.
- Textured surfaces give better point clouds; a stable mount helps scans.
- **Running over SSH (Jetson):** To show OpenCV windows on the Jetson display when SSH'd from a laptop, run:
  ```bash
  DISPLAY=:0 XAUTHORITY=/run/user/$(id -u)/gdm/Xauthority python3 realsense_view.py
  ```
  (Adjust `XAUTHORity` path if needed for your login session.)

---

## Known limitations

- D455 depth is less stable at very close range (&lt;0.5 m).
- `radar_mapper.py` is memory-heavy; watch Jetson RAM if you run other workloads.
- Do not commit `scan.npz`; add `*.npz` to `.gitignore` if needed.

---

## Future work

- **Navigation module** — From obstacle data to a decision: left/right free space → safest direction → command (e.g. FORWARD / TURN LEFT / TURN RIGHT / STOP).
- **Object detection + depth** — YOLOv8 / TensorRT / ONNX fused with depth (e.g. "person, 1.8 m, approaching").
- **Persistent 3D map** — Depth → point cloud accumulation → voxel grid → saved map file.
- ROS2 publishing, SLAM, GPU-accelerated depth, drone pipelines.

---

## License

MIT License
