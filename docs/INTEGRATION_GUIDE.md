> Current architecture and milestone status are maintained in
> [PROJECT_PLAN.md](PROJECT_PLAN.md), [ENVIRONMENT_CONTRACT.md](ENVIRONMENT_CONTRACT.md)
> and [RESUME_HERE.md](RESUME_HERE.md). The sections below describe the original
> bench-report interface, which remains separate from full environment packages.

# Integration guide for sibling repositories

This repository owns the depth-health policy and produces portable replay
reports. Sibling projects should consume those reports or a future adapter API;
they should not copy the policy into their own JavaScript, Python, or vehicle
control code.

## Machine-to-machine workflow

After this feature branch is reviewed and pushed, use the same Git branch or
commit on each machine:

```bash
git clone https://github.com/abelxmendoza/Jetson-RealSense-Perception.git
cd Jetson-RealSense-Perception
git switch codex/recorded-run-dashboard
python3 -m unittest discover -s tests -v
```

On Linux, launch with:

```bash
./scripts/open_bench_dashboard_linux.sh
```

The launcher binds the server to `127.0.0.1`, starts a browser when a desktop
opener is available, and stores process/log files under `.bench_dashboard/`.
Set `BENCH_DASHBOARD_PORT` if port 8765 is already in use.

## Produce a portable report

```bash
python3 scripts/replay_bench.py recording.jsonl --output bench-report.json
```

The output conforms to `schemas/bench-replay-report-v1.schema.json`. Consumers
must check both:

```python
import json

with open("bench-report.json", encoding="utf-8") as handle:
    report = json.load(handle)

if report.get("report_type") != "bench_replay_report":
    raise ValueError("not a depth bench replay report")
if report.get("schema_version") != 1:
    raise ValueError("unsupported replay report schema")

for event in report["events"]:
    print(event["timestamp_s"], event["status"], event["fault_reason"])
```

Consumers should preserve `SKIP` as its own outcome and preserve the recording
source label. A synthetic report must never be relabeled as hardware evidence.

## Repository boundaries

### PX4 project

Planned role: consume recorded reports in simulation or verification tooling.
It may assert state sequences and timing, but this repository does not send
PX4 commands and the report is not proof of flight safety.

### Omega1 project

Planned role: a rover adapter will translate perception states after hardware
repair. The adapter must fail safe on `SENSOR_FAULT`. Motor commands and rover
control remain outside this repository.

### RealmForge project

Planned role: consume future raw RGB-D recordings and calibration. The current
health-summary JSONL does not contain pixels, point clouds, intrinsics, or
extrinsics and must not be presented as environment reconstruction.

### Additional repositories

Use the same report boundary when a project needs evaluated perception history.
If it needs raw sensor data or live events, define a separate versioned contract
rather than stretching the v1 replay report.

## Parallel agent work

Agents can work on separate repositories at the same time once each task has:

1. an exact checkout path and target branch;
2. a bounded deliverable, such as “read v1 reports in the PX4 simulator”;
3. an explicit interface version (`bench_replay_report`, schema version 1);
4. independent tests and a no-push/no-merge boundary unless authorized.

Keep one owning agent responsible for contract changes here. Consumer agents
should not silently change the producer schema to make their repository easier.
