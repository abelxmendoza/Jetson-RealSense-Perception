# Jetson RealSense Perception Toolkit

A robotics perception toolkit built for the **NVIDIA Jetson Orin Nano** using the **Intel RealSense D455 RGB-D camera**.

This project demonstrates core perception capabilities used in **autonomous robots and drones**, including:

- RGB-D sensing
- Real-time obstacle detection
- 3D point cloud capture
- Feature tracking
- IMU streaming
- Real-time occupancy grid mapping

The scripts in this repository explore how depth cameras can be used for **robot navigation, environment perception, and 3D mapping**.

---

## Hardware

- NVIDIA Jetson Orin Nano
- Intel RealSense D455 RGB-D Camera

---

## System Architecture

```
RealSense Camera
       ↓
librealsense SDK
       ↓
pyrealsense2 Python bindings
       ↓
OpenCV / NumPy Processing
       ↓
Perception Modules
  • obstacle detection
  • point cloud capture
  • feature tracking
  • occupancy mapping
```

---

## Scripts

### 1. `realsense_view.py` — Basic Viewer

Simple RGB and depth stream viewer. This is the **starting point** for verifying camera operation.

**Usage:**

```bash
python3 realsense_view.py
```

Press `q` to quit.

---

### 2. `obstacle_detector.py` — Navigation Helper

Real-time obstacle detection with distance warnings. A navigation zone in the center of the image is monitored for objects that are too close.

**Usage:**

```bash
python3 obstacle_detector.py
```

**Features:**

- Yellow rectangle shows the monitored navigation zone
- Green text = clear path
- Red text = obstacle detected (< 0.5m)
- Press `q` to quit

---

### 3. `point_cloud_capture.py` — 3D Scanning

Capture 3D point clouds from the camera and save them for later visualization.

**Usage:**

```bash
python3 point_cloud_capture.py
```

**Controls:**

- Press `s` to save the current frame as a point cloud
- Press `q` to quit

Saved scans are stored as: `scan.npz`

---

### 4. `view_scan.py` — Point Cloud Viewer

Visualize saved point cloud scans in 3D.

**Requirements:**

```bash
pip3 install open3d
```

**Usage:**

```bash
python3 view_scan.py [scan_file.npz]
```

If no file is specified, the script defaults to: `scan.npz`

---

### 5. `simple_tracking.py` — Feature Tracking

Basic visual feature tracking between frames. This demonstrates how cameras can estimate motion by tracking features across images.

**Usage:**

```bash
python3 simple_tracking.py
```

**Features:**

- Displays feature matches between consecutive frames
- Prints tracking statistics to console
- Press `q` to quit

---

### 6. `imu_stream.py` — IMU Data Streaming

Stream and visualize accelerometer and gyroscope data from the RealSense camera's built-in IMU.

**Usage:**

```bash
python3 imu_stream.py
```

**Features:**

- Real-time graphs of accelerometer (X, Y, Z)
- Real-time graphs of gyroscope (X, Y, Z)
- Pitch and roll estimation from accelerometer data
- Motion magnitude calculation

**Controls:**

- Press `s` to save IMU data to file
- Press `q` to quit

**Note:** This script requires a RealSense camera with IMU support (D435i, D455, etc.).

---

### 7. `radar_mapper.py` — 3D Radar Mapper

Live 3D occupancy grid mapper with a radar-style visualization. The script builds a map in real time as the camera scans the environment.

**Usage:**

```bash
python3 radar_mapper.py
```

**Features:**

- Top-down radar view showing occupied space
- Side view (X-Z plane visualization)
- Live RGB and depth feed
- Occupancy grid mapping
- 2 cm resolution grid

**Controls:**

- Press `c` to clear the map
- Press `s` to save the map
- Press `q` to quit

**Additional features:**

- Real-time 3D mapping
- Radar-style circular range indicators
- Accumulates points over time to build a complete map
- Confidence-based point coloring

---

## Getting Started

1. **Verify camera functionality**
   ```bash
   python3 realsense_view.py
   ```

2. **Test obstacle detection**
   ```bash
   python3 obstacle_detector.py
   ```

3. **Capture a 3D scan**
   ```bash
   python3 point_cloud_capture.py
   ```

4. **Visualize the scan**
   ```bash
   python3 view_scan.py
   ```

5. **Explore motion tracking**
   ```bash
   python3 simple_tracking.py
   ```

6. **View IMU data (if supported)**
   ```bash
   python3 imu_stream.py
   ```

7. **Run the radar mapper**
   ```bash
   python3 radar_mapper.py
   ```

---

## Requirements

- **Python 3**

**Required packages:**

- `pyrealsense2`
- `numpy` (<2.0 for compatibility)
- `opencv-python`

**Optional:**

- `open3d`

**Install dependencies:**

```bash
pip3 install numpy opencv-python open3d
```

---

## Tips

- Ensure RealSense firmware is up to date
- Good lighting improves depth sensing performance
- Ideal sensing range is approximately 0.3m to 10m
- Point clouds work best on textured surfaces
- Use a tripod or stable mount for better scans

---

## Future Work

Potential extensions for this project include:

- ROS2 sensor publishing
- SLAM integration
- GPU-accelerated depth processing
- RGB-D object detection
- Autonomous navigation experiments
- Drone perception pipelines

---

## License

MIT License
