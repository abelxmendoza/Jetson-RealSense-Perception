# Perception environment package v1

Status: implemented producer baseline; consumer adoption pending. The format
name remains `perception_scan` to match existing prototypes. Version 1 additions
are optional; changing required semantics requires a new version.

## Required manifest fields

`manifest.json` is a JSON object containing:

- `package_type`: `perception_scan`; `schema_version`: integer `1`.
- `source`: `synthetic`, `hardware`, or `dataset`; this is declared provenance,
  not independent authentication of sensor origin.
- `pose_source`: `ground_truth`, `external`, or `rtabmap`.
- `units`: `metres`; `frame`: `map`.
- `axes`: x forward, y left, z up (right handed).
- `T_realmforge_map`: rigid map-to-RealmForge transform. Currently maps
  `(x,y,z)` to `(-y,z,-x)`; consumers apply once and verify their convention.
- `files`: semantic roles mapped to relative package-local filenames. At least
  `point_cloud` (PLY) and `occupancy` (ROS-style YAML) are present currently.

Paths must resolve to actual files inside the package. Absolute paths and
traversal outside the package are invalid. Unsupported versions/units/frames
must be rejected. Calibration and pose arrays are required only when exporting
raw posed depth; absent fields must not be fabricated.

## Optional products

| Role | Format | Semantics |
| --- | --- | --- |
| point_cloud | PLY | metric points in map coordinates; not necessarily a surface |
| mesh | OBJ | currently untextured visual surface; not automatically valid collision geometry |
| occupancy | YAML referencing PGM | 2D navigation input, not drone free-space evidence |
| trajectory | JSON | timestamped T_map_camera, optical camera to map |
| calibration | JSON | width, height, fx, fy, cx, cy |
| depth_sequence | NPZ | depth_m[N,H,W], T_map_camera[N,4,4], timestamp_s[N] |

Depth uses axial z metres and optical axes right/down/forward. Timestamps are
finite, nonnegative, strictly increasing within a posed sequence. Poses are
finite right-handed rigid transforms. RGB/textures, semantic labels, collision
assets, coordinate uncertainty, and georeferencing are not yet standardized.

## Occupancy baseline

Producer metadata `occupancy` includes resolution_m, origin_xy, height_band_m
and unknown_preserved. PGM is P5, 8-bit: occupied=0, free=254, unknown=205.
File top row is largest map y. YAML origin gives the bottom-left corner;
cell centres are origin + (index + 0.5)*resolution. Unknown is blocked for
conservative planning. Height-band projection is a prototype, not certified
traversability; it cannot establish full robot-body or drone clearance.

Visual reconstruction, collision geometry, rover traversability and drone
clearance are distinct products. Never silently turn a mesh or splat into
trusted collision/navigation data. A Gaussian-splat PLY is not an ordinary
point-cloud PLY simply because the filename extension matches.

## Consumers

Consumers own their adapters and runtime behavior. They must preserve provenance,
check version/frames, and remain runnable without the producer repo. This repo's
consumer exporters are experimental fixture generators only. Environment export
must not start physical motion or alter live robot configuration.
