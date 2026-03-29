# Real-Time Depth-Based Obstacle Awareness System (Jetson + ROS2)

<p align="center">
  <img src="./Jetson-RealSense-PerceptionProject.png" alt="Jetson RealSense Perception" width="700"/>
</p>

<p align="center">
  <img src="./JetsonVision.jpeg" alt="Jetson Vision" width="700"/>
</p>

A **hardware-first** real-time perception and reactive control system running on **NVIDIA Jetson Orin Nano** + **Intel RealSense D455**, built entirely in C++ with ROS2 Humble. The system reads live depth data, detects obstacles, makes directional avoidance decisions, and visualizes everything in RViz2 — no simulation required.

---

## System Pipeline

```
Intel RealSense D455
        │
        │  PointCloud2  (/camera/depth/color/points)
        ▼
┌─────────────────────┐
│   obstacle_node     │  C++ — PointCloud2Iterator (no PCL)
│   (C++ ROS2 node)   │
└─────────────────────┘
        │                          │
        │  ObstacleArray           │  MarkerArray
        │  (/obstacles)            │  (/obstacle_markers)
        ▼                          ▼
┌─────────────────────┐      ┌──────────────────┐
│   control_node      │      │     RViz2         │
│   (C++ ROS2 node)   │      │                  │
└─────────────────────┘      │  • Point cloud   │
        │                    │  • Colored spheres│
        │  Twist             │  • Velocity arrow │
        │  (/cmd_vel)        │  • TF tree        │
        ▼                    │  • Robot model    │
   /cmd_vel_marker ──────────┤                  │
                             └──────────────────┘
```

**What you see in RViz:**
- Live depth point cloud from the D455
- Obstacle spheres colored by distance: **RED** < 0.5m | **YELLOW** < 1.0m | **GREEN** ≥ 1.0m
- **Blue arrow** showing current velocity command (forward or turning direction)
- TF tree showing `base_link → camera_link` transform

---

## Hardware Stack

| Layer | Component |
|-------|-----------|
| **Compute** | NVIDIA Jetson Orin Nano |
| **OS** | Ubuntu 22.04 / JetPack L4T 36.4.7 |
| **Camera** | Intel RealSense D455 (RGB-D + IMU) |
| **SDK** | librealsense 2.x — built from source with RSUSB backend |
| **ROS2** | Humble |
| **Camera driver** | realsense2_camera (realsense-ros) |

---

## Quick Start

### 1. Build

```bash
cd ~/path/to/this/repo
colcon build --symlink-install
source install/setup.bash
```

### 2. Launch everything (one command)

```bash
ros2 launch jetson_realsense_perception autonomy_stack.launch.py
```

### 3. Open RViz with pre-built config

```bash
rviz2 -d config/autonomy.rviz
```

All displays are pre-configured. You will immediately see the point cloud, colored obstacle spheres, and velocity arrow.

### 4. Override parameters at launch

```bash
ros2 launch jetson_realsense_perception autonomy_stack.launch.py \
  safe_distance:=1.5 \
  forward_speed:=0.3 \
  turn_rate:=0.4 \
  sample_stride:=16
```

### 5. Tune parameters at runtime (no restart needed)

```bash
ros2 param set /control_node safe_distance 1.2
ros2 param set /obstacle_node sample_stride 4
```

---

## ROS2 Topics

| Topic | Type | Published by |
|-------|------|-------------|
| `/camera/depth/color/points` | `sensor_msgs/PointCloud2` | realsense2_camera |
| `/obstacles` | `obstacle_interfaces/ObstacleArray` | obstacle_node |
| `/obstacle_markers` | `visualization_msgs/MarkerArray` | obstacle_node |
| `/cmd_vel` | `geometry_msgs/Twist` | control_node |
| `/cmd_vel_marker` | `visualization_msgs/Marker` | control_node |

---

## ROS2 Parameters

### obstacle_node

| Parameter | Default | Description |
|-----------|---------|-------------|
| `sample_stride` | `8` | Process every Nth point. D455 at 640×480 = 307k pts/frame; stride=8 → ~38k pts |

### control_node

| Parameter | Default | Description |
|-----------|---------|-------------|
| `safe_distance` | `1.0` | Distance (m) below which robot stops and turns |
| `critical_distance` | `0.5` | Emergency threshold — obstacle is very close |
| `forward_speed` | `0.5` | Forward velocity in m/s |
| `turn_rate` | `0.5` | Rotation velocity in rad/s |

---

## Package Structure

```
src/
  obstacle_interfaces/          # Custom ROS2 message definitions
    msg/Obstacle.msg            # x, y, z, distance
    msg/ObstacleArray.msg       # stamped Header + Obstacle[]

  obstacle_perception/          # C++ perception node
    src/obstacle_node.cpp       # PointCloud2 → ObstacleArray + MarkerArray

  robot_control/                # C++ control node
    src/control_node.cpp        # ObstacleArray → cmd_vel + velocity marker

  robot_description/            # URDF + TF
    urdf/robot.urdf             # base_link → camera_link (fixed joint, 20cm above)
    launch/robot_state_publisher.launch.py

  standalone/                   # Python validation scripts (no ROS)
    obstacle_detector.py
    realsense_view.py
    imu_stream.py
    radar_mapper.py
    point_cloud_capture.py
    ...

launch/
  autonomy_stack.launch.py      # Full system — one command
config/
  autonomy.rviz                 # Pre-built RViz config
  realsense.yaml                # Camera driver config
```

---

## Design Decisions

### Hardware-first, no simulation
Every feature in this stack is validated live against the D455 on the Jetson. There is no Gazebo dependency, no URDF simulation, no mock sensor data. This forces real constraints to surface early — USB bandwidth, Jetson GPU/CPU limits, actual depth noise profiles — rather than discovering them after simulation work is sunk.

### No PCL
PCL is a large dependency that is slow to compile, has version friction with ROS2 Humble on Jetson, and is unnecessary for this use case. `sensor_msgs::PointCloud2Iterator<float>` provides direct, stride-safe typed access to XYZ fields with zero copy and no external library. Everything from distance calculation to downsampling is plain C++ arithmetic.

### Downsampling by stride, not voxel grid
The D455 at 640×480 produces ~307,000 points per frame. Rather than voxel-filtering (which requires spatial indexing), we sample every Nth point during iteration. This is O(N), cache-friendly, and deterministic. The default stride of 8 reduces the working set to ~38k points — sufficient for reactive avoidance and well within Jetson's real-time budget.

### Reactive control baseline
The control logic is intentionally simple: stop if something is within `safe_distance`, turn away from the obstacle's lateral position (y > 0 → obstacle is left → turn right). This deterministic policy is fast to reason about, easy to debug on hardware, and is the correct foundation before adding anything more complex (potential fields, VFH, Nav2).

### Marker lifetime instead of DELETE_ALL
Obstacle markers are published with a 300ms lifetime. At 30fps the camera sends new data every 33ms, so fresh markers always arrive well before old ones expire. If the camera stops, all markers auto-clear within 300ms. This avoids the bookkeeping complexity of tracking and deleting individual marker IDs across frames.

---

## Standalone Validation Scripts (no ROS)

Use these to verify hardware and SDK before touching ROS:

```bash
# Verify D455 is detected
python3 scripts/check_realsense.py

# Headless capture (SSH-safe)
python3 scripts/capture_color_depth.py -o assets/sample_outputs

# Live obstacle detection (standalone, no ROS)
python3 src/standalone/obstacle_detector.py --no-gui

# IMU stream (headless)
python3 src/standalone/imu_stream.py --no-gui
```

---

## Hardware Notes

- **Camera lock** — Only one process can open the D455 at a time. If `ros2 launch` is running, standalone pyrealsense2 scripts will fail with a busy device error. Kill one before starting the other.
- **Headless Jetson** — `cv2.imshow()` and rqt fail without a display. Use `--no-gui` flags on standalone scripts or connect via RViz2 on your laptop with `ROS_DOMAIN_ID` set.
- **USB** — D455 requires USB 3.x for full-resolution streaming. USB 2 will cause frame drops or launch failures.
- **pointcloud.enable** — This parameter **must be `True`** in the camera launch. If it is false, `/camera/depth/color/points` will not publish and `obstacle_node` will receive nothing.

---

## Docs

| Doc | Purpose |
|-----|---------|
| [docs/hardware_setup.md](docs/hardware_setup.md) | Jetson, D455, USB, headless |
| [docs/software_setup.md](docs/software_setup.md) | librealsense from source (RSUSB), pyrealsense2 |
| [docs/ros2_setup.md](docs/ros2_setup.md) | Workspace, realsense-ros, launch |
| [docs/troubleshooting.md](docs/troubleshooting.md) | Common Jetson + RealSense + ROS2 fixes |
| [docs/validation.md](docs/validation.md) | Step-by-step validation commands |

---

## License

MIT. See [LICENSE](LICENSE).
