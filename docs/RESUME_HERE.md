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
