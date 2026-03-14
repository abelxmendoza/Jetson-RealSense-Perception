# Intel RealSense Playground

A collection of scripts to explore navigation, 3D scanning, and robotics with Intel RealSense cameras.

## Scripts

### 1. `realsense_view.py` - Basic Viewer
Simple RGB and depth stream viewer. Your starting point.

**Usage:**
```bash
python3 realsense_view.py
```
Press 'q' to quit.

---

### 2. `obstacle_detector.py` - Navigation Helper
Real-time obstacle detection with distance warnings. Shows if objects are too close in the center navigation zone.

**Usage:**
```bash
python3 obstacle_detector.py
```
- Yellow rectangle shows the navigation zone being monitored
- Green text = clear path
- Red text = obstacle detected (< 0.5m)
- Press 'q' to quit

---

### 3. `point_cloud_capture.py` - 3D Scanning
Capture 3D point clouds from the camera. Save scans for later viewing.

**Usage:**
```bash
python3 point_cloud_capture.py
```
- Press 's' to save the current frame as a point cloud
- Press 'q' to quit
- Saved scans are stored as `scan.npz`

---

### 4. `view_scan.py` - Point Cloud Viewer
Visualize saved point cloud scans in 3D.

**Requirements:**
```bash
pip3 install open3d
```

**Usage:**
```bash
python3 view_scan.py [scan_file.npz]
```
If no file is specified, defaults to `scan.npz`.

---

### 5. `simple_tracking.py` - Feature Tracking
Basic visual feature tracking for understanding camera movement. Shows how features are matched between frames.

**Usage:**
```bash
python3 simple_tracking.py
```
- Shows feature matches between consecutive frames
- Prints tracking statistics to console
- Press 'q' to quit

---

### 6. `imu_stream.py` - IMU Data Streaming
Stream and visualize accelerometer and gyroscope data from the RealSense camera's built-in IMU.

**Usage:**
```bash
python3 imu_stream.py
```
- Real-time graphs of accelerometer (X, Y, Z) and gyroscope (X, Y, Z) data
- Calculates pitch and roll from accelerometer
- Shows motion magnitude
- Press 's' to save IMU data to file
- Press 'q' to quit

**Note:** Requires a RealSense camera with IMU (D435i, D455, etc.)

---

### 7. `radar_mapper.py` - 3D Radar Mapper
Live 3D occupancy grid mapper with radar-style top-down view. Builds a map in real-time as you scan with the camera.

**Usage:**
```bash
python3 radar_mapper.py
```
- **Top-down radar view**: Green dots show occupied space (like a radar sweep)
- **Side view**: X-Z plane visualization
- **Live camera feed**: RGB and depth streams
- **Occupancy grid**: 2cm resolution grid showing free/occupied space
- Press 'c' to clear the map
- Press 's' to save the map
- Press 'q' to quit

**Features:**
- Real-time 3D mapping as you move the camera
- Radar-style circular range indicators
- Accumulates points over time to build a complete map
- Visual feedback with confidence-based coloring

---

## Getting Started

1. **Start simple:** Run `realsense_view.py` to verify your camera works
2. **Try navigation:** Run `obstacle_detector.py` to see distance detection
3. **Capture scans:** Use `point_cloud_capture.py` to save 3D data
4. **View scans:** Install open3d and use `view_scan.py` to visualize
5. **Explore tracking:** Run `simple_tracking.py` to see feature matching
6. **IMU data:** Run `imu_stream.py` to see motion sensors (if your camera has IMU)
7. **3D mapping:** Run `radar_mapper.py` for live occupancy grid mapping

## Requirements

- Python 3
- `pyrealsense2` (Intel RealSense SDK Python bindings)
- `numpy` (< 2.0 for compatibility)
- `opencv-python` (cv2)
- `open3d` (optional, for `view_scan.py`)

## Tips

- Make sure your camera firmware is up to date
- Good lighting helps with depth sensing
- For best results, keep objects 0.3m - 10m from the camera
- Point clouds work best with textured surfaces
