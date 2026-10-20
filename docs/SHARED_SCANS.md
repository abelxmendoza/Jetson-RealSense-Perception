# Shared scans for Omega1 and RealmForge

## Working now

Run from this repository on Linux, without a camera or ROS:

```bash
python3 scripts/build_scan.py /tmp/room-scan --frames 36 --mesh
```

Requires NumPy and, for `--mesh`, Open3D (already installed on this machine).
The output directory must be new. Omitting `--mesh` skips Open3D. The scan is a
raycast room with a static cuboid, observed from known camera poses. Open3D TSDF
fusion reconstructs the OBJ from those depth images; it is not the simulator's
original scene mesh. This is an export/integration test, not SLAM validation.

## Package v1

`manifest.json` declares source, units, axes, pose provenance and relative files.

| File | Role |
| --- | --- |
| cloud.ply | Accumulated world-frame point cloud |
| mesh.obj | Optional untextured reconstructed triangle surface |
| map.yaml + map.pgm | ROS-style occupancy map with unknown cells preserved |
| poses.json | Timestamped camera-to-map transforms |
| camera.json | Pinhole intrinsics |
| rgbd.npz | Metric depth sequence, timestamps and camera-to-map transforms |

Map axes are x forward, y left, z up. Depth uses optical axes x right, y down,
z forward and axial z metres. Open3D integration receives the inverse pose,
because its extrinsic is map-to-camera. The manifest supplies a rigid transform
for a proposed RealmForge convention: x right, y up, negative z forward:
`(x, y, z)_map -> (-y, z, -x)_realmforge`. Apply once to a parent object, keeping
mesh geometry, camera poses and map overlays aligned. Confirm the actual
consumer world convention before importing.

The occupancy map uses the world-height band 0.15–1.5 m. Rays mark observed
free space and occupied endpoints; occupied evidence wins. Image rows are
flipped relative to increasing map y. This simple static-map exporter does not
handle moving objects, slopes, robot footprint inflation or loop-closure updates.
Unobserved space is not assumed free. It is not a drop-in validated navigation
system.

## External posed depth

```bash
python3 scripts/build_scan.py /tmp/external-scan \
  --input-npz /path/frames.npz --camera-json /path/camera.json \
  --source dataset --mesh
```

NPZ keys: `depth_m` [N,H,W], `T_map_camera` [N,4,4], `timestamp_s` [N].
The calibration JSON contains `width,height,fx,fy,cx,cy`. Input poses must already
be calibrated, rigid, in the declared z-up map frame and share a clock with the
strictly increasing timestamps. The source flag records operator provenance; it
cannot authenticate the data. Raw RealSense data needs SDK unit conversion and
pose estimation first. This adapter accepts already posed data, not raw bags.

## RTAB-Map bridge

Official references:

- https://github.com/introlab/rtabmap_ros/tree/ros2
- https://introlab.github.io/rtabmap/api/latest/tools.html
- https://introlab.github.io/rtabmap/api/latest/parameters.html
- https://www.open3d.org/docs/release/tutorial/pipelines/rgbd_integration.html

RTAB-Map supplies odometry, loop closure and exports; we do not reimplement those.
On this machine ROS 2 Humble exists, but RTAB-Map was not installed during this
change. Before installation, check the OS/ROS compatibility and apt package
availability. Before camera configuration, confirm the RealSense model and SDK.

Use `rtabmap-export --help` for the installed release's exact flags, or export
via RTAB-Map/databaseViewer. Obtain a PLY cloud, ROS map YAML/PGM and optionally
an **untextured, self-contained OBJ** in the same z-up map frame. Then:

```bash
python3 scripts/package_rtabmap.py /tmp/house-scan \
  --cloud /path/export.ply --map-yaml /path/map.yaml \
  --map-image /path/map.pgm --mesh /path/export.obj --source hardware
```

The bridge copies exports into a portable package and rewrites the map image
reference. It does not run SLAM, validate RTAB-Map geometry, infer transforms,
convert bags, or bundle OBJ materials/textures. External exports must share a
map origin. No camera poses are fabricated when the exports do not include them.

## Consumer status

Omega1 can use the ROS-style occupancy assets after a consumer adapter validates
manifest version, source, units and frame, then handles robot localization and
map-to-robot transforms. RealmForge needs an importer for the manifest and its
PLY/OBJ geometry plus collision setup. Neither sibling repository was modified
by this change, so end-to-end imports are not yet implemented or verified.
The next milestone is those two importer adapters, then a recorded real RGB-D
sequence through RTAB-Map, followed by a physical one-room scan.
