# Resume here

Read AGENTS.md, PROJECT_PLAN.md and ENVIRONMENT_CONTRACT.md before editing.
Updated 2026-10-19, Los Angeles time.

## Current state

- Original main is 6090bf9; fetched Mac work is on
  origin/codex/recorded-run-dashboard at c0c2d44. Branch files were extracted into
  the working tree because this session cannot modify .git. They are not merged.
- Local additions: offline replay/dashboard, depth simulator, known-pose room
  fusion with optional Open3D TSDF mesh, shared scan export and RTAB-Map export
  packaging. RTAB-Map itself is not installed; ROS Humble/Open3D are present here.
- Experimental consumer prototypes: scan_consumers.py and export_consumers.py.
  They are not wired into sibling applications. Move application ownership to
  consumer repos when implementing the real adapters.
- Existing standalone script changes predate this work and must be preserved.
- No push/commit has occurred in this session; other machines will not see these
  files until the user commits/pushes and pulls them there.

## Commands

```bash
python3 -m unittest discover -s tests -v
python3 scripts/simulate_depth.py --headless
python3 scripts/build_scan.py /tmp/new-room-scan --frames 24 --mesh
python3 scripts/validate_scan.py /tmp/new-room-scan
```

Use a new output directory per scan. Open3D is optional except for --mesh.
HTTP tests may be blocked in restricted sessions: do not count them as passed.
Physical camera, GUI, RTAB-Map, Gazebo, RealmForge import and Omega integration
have not been validated by the producer tests.

## Next gate

Finish validating/stabilizing the producer contract, then implement native scan
import and visual/collision separation in RealmForge in a writable RealmForge
session. Use PROJECT_PLAN.md milestone order. Keep all four projects sovereign.

## Latest validation

- 30 core Python tests pass. Two dashboard HTTP tests cannot start because the
  current execution sandbox denies socket creation; full discovery reports a
  setUpClass error. Do not turn this into a skip that hides real CI failures.
- Python compileall, Linux launcher syntax and git diff whitespace checks pass.
- A fresh 12-view Open3D mesh package generated and passed validate_scan.py.
- Experimental consumer export produced RealmForge blocker JSON and an Omega
  occupancy/route example. These files have not been opened by either consumer.
- Producer exports now self-validate. Package-local path traversal/symlinks,
  mismatched trajectory/depth poses, unsupported versions, map metadata and
  invalid units/frames are covered by tests.
- Dependencies are split into requirements-offline.txt and optional
  requirements-mapping.txt. CI builds/validates a small mesh-free environment.
- Remaining work: production importer in RealmForge, collision asset decisions,
  Gazebo world export and runtime tests; later Omega and PX4 adapters. No real
  camera/SLAM/sensor-fusion result is implied by the synthetic evidence.

## Cross-repository continuation (2026-10-19)

The user committed/pushed the producer work as ab361f2 on
feature/shared-environments. All four GitHub CI jobs passed (Ubuntu/macOS,
Python 3.10/3.12), including HTTP tests unavailable in the local sandbox.

RealmForge remote main was 37 commits ahead of its desktop copy. The importer
was tested with remote main b64409d, preserving its existing property/GLB scan
features. Draft PR: https://github.com/abelxmendoza/RealmForge-XR/pull/46
Branch: feature/perception-scan-map-import; commit c946b3c.
Validation there: 474 tests, TypeScript, and production build passed.

The new RealmForge importer loads selected manifest/YAML/PGM files into native
metric navigation proxies. It retains unknown blockers and existing replacement
confirmation. It does NOT automatically import/align mesh visuals, export Gazebo
worlds, or integrate Omega/PX4. Browser/headset rendering remains unverified.

Next: review PR 46; test the actual browser import; connect existing GLB visuals
and navigation proxies without losing metric alignment, then pursue the Gazebo
milestone. Original desktop RealmForge checkout was not modified. Updates from
this point were published through the GitHub connector; fetch current remote
branches before continuing from older local commits.

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
