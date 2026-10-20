# Agent handoff — read before changing this repository

Read `docs/PROJECT_PLAN.md`, `docs/ENVIRONMENT_CONTRACT.md`, and
`docs/RESUME_HERE.md` first. These are the cross-machine source of project intent.
Update the handoff after meaningful work; distinguish tested behavior from plans.

## User-approved architecture

Four sovereign repositories connect through optional, versioned data interfaces:
Jetson-RealSense-Perception (capture/reconstruction), RealmForge-XR (world editing,
phone/Scaniverse imports and simulation preparation), Omega-Code (rover), and
PX4-Autonomous-Missions (drone missions/verification). Gazebo runs physics/sensors.
No project requires sibling checkouts, matching branches, or a central service.
Adapters belong in consumers. Consumer prototypes here are experimental examples,
not an excuse to move rover control or RealmForge business logic into perception.

RealSense is initially an external environment scanner, not a rover-mounted
sensor. Physical Omega1 still needs localization and live obstacle sensing.
Phone/Scaniverse input is independent of RealSense; multi-source alignment/fusion
is a later milestone. Keep appearance, collision geometry, 2D traversability and
3D clearance distinct. Never label synthetic data as hardware evidence or
known-pose fusion as SLAM. Never infer free space merely from absent points.

## Execution

Continue authorized milestones without repeatedly asking for permission. Respect
explicit requests to plan before editing. Preserve unrelated user changes.
At handoff creation the three `src/standalone/{obstacle_detector,radar_mapper,
realsense_view}.py` files contained pre-existing local edits: do not overwrite or
silently include them in a commit. Check current status; this note is historical.

Use offline Python tests for core work. HTTP tests require local socket access;
report restricted-environment failures accurately. Open3D is optional for meshes;
core CI must not require camera hardware, ROS, a display, or sibling repositories.
Do not commit large scans or private room captures. No cloud uploads by default.

Notes reach other machines only after commit/push and pull. Never claim a sync,
merge, deployment, hardware test, or sibling integration happened without evidence.

## General-purpose RealSense support and shared ownership

RealmForge-XR is a shared team project. RealSense environment support is a
reusable feature for any user with a compatible capture setup, not an Abel-only
integration or a dependency on Omega1/PX4. Keep RealmForge changes as reviewable
team proposals; do not merge or repurpose the project without authorization.

The independent core path is capture/reconstruction -> versioned environment
package -> neutral package-to-Gazebo conversion -> robot-specific consumers.
RealmForge is an optional authoring/import/export participant. A Gazebo exporter
must be usable without RealmForge. Existing phone/Scaniverse and authored-world
workflows remain standalone; RealSense users need neither phone scans nor the
personal robot repositories.

Public user workflow: capture with a compatible external RealSense tool, export
a validated metric package, import it into RealmForge, inspect/align visual and
navigation layers, and export supported environment assets. Initial support is
file-based; direct browser USB capture, automatic raw-camera reconstruction,
mesh/map alignment, multi-source fusion and Gazebo export are not implemented
by the current map importer. Do not advertise those as available.

Adapters validate contracts, not personal filesystem paths, device names or
robot identities. Hardware compatibility must be documented per tested model
and SDK/OS combination rather than claiming every RealSense device is supported.
