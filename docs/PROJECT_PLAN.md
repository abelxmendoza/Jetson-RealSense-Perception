# Shared environments — approved roadmap

Updated 2026-10-19 (America/Los_Angeles).

## Goal

Capture a real room, prepare it in RealmForge, load it into Gazebo, and test
Omega1 and PX4 missions in the same measured environment. Later, simulated
survey missions collect RGB-D observations that reconstruct a new environment;
compare reconstruction against simulation ground truth. All projects remain
standalone. No additional repository or cloud backend is required initially.

## Ownership

| Repository | Owns | Optional exchange |
| --- | --- | --- |
| Jetson-RealSense-Perception | calibration, acquisition, pose-backed reconstruction, scan validation | neutral environment packages and observations |
| RealmForge-XR | world authoring, phone/Scaniverse import, visual/collision preparation | import package, export Gazebo assets |
| Omega-Code | rover localization, planning, control, existing SIL | map/world adapter; later Gazebo robot integration |
| PX4-Autonomous-Missions | drone missions, surveys, verification | world adapter and recorded sensor observations |

Gazebo is the physics and simulated-sensor runtime. RealmForge and Gazebo must
not be described as equivalent simulation engines. A saved map does not provide
robot localization or detect furniture that moved after scanning.

## Milestones and gates

1. **Stabilize perception prototypes and environment contract v1.** Validate files,
   units, transforms, provenance and dependency boundaries. Preserve user changes.
2. **RealmForge reference-room import.** Correct scale/orientation; visual mesh
   separate from collision data. Implement the real adapter in RealmForge.
3. **Gazebo static-world export.** Valid world/model resources and simplified
   collision geometry; sensor observations consistent with source geometry.
4. **Omega1 integration.** Preserve current kinematic/ArUco SIL. Add occupancy
   loading, footprint checks, map-frame alignment and a separate Gazebo workflow.
5. **Real living-room scan.** Confirm camera model and ROS/SDK compatibility;
   configure RTAB-Map odometry/loop closure; inspect scale, gaps and repeatability.
6. **PX4 shared-world integration.** Larger suitable reference world first;
   configure sensors, frame transforms and existing mission verification.
7. **Survey/reconstruction loop.** Record calibrated depth/poses from simulated
   survey missions. Measure coverage and reconstruction error, not just route
   completion. Known-pose and estimated-pose results are separate evidence.
8. **Multiple capture sources.** Independent phone/Scaniverse and RealSense
   importers first. Align captures, validate errors, then selectively fuse.

First end-to-end gate: one reference room opens in RealmForge and Gazebo, and
simulated Omega1 avoids the same obstacle at matching metric coordinates.
No Gazebo integration, real SLAM, physical rover navigation or scan fusion has
yet passed that gate.

## Efficient workflow

File exchange before live services. Small fixtures rather than sibling imports.
Each consumer supports the contract version independently. Breaking contract
changes require a version bump and migration notes; no synchronized releases.
Keep synthetic/hardware/dataset labels and measured/estimated pose provenance.
Check both standalone regression and integration behavior in every consumer.

## Machine handoff

Commit this plan, AGENTS.md, contract, code and relevant tests together on a
review branch, excluding unrelated edits and private/large data. Push and pull
on each machine. No tool or agent memory substitutes for repository sync.
Sibling repositories need their own local handoff referencing this contract when
we work in them; they have not been modified from this workspace.
