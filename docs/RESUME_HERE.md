# Resume here: recorded-run dashboard

## Project location

```text
/Users/abel_elreaper/Desktop/projects/Jetson-RealSense-Perception
```

The dashboard is on branch `codex/recorded-run-dashboard`. It is a local-only
recorded-run inspector and needs only the Python 3 included with macOS. It does
not need ROS, a Jetson, a RealSense camera, API keys, or paid services.

## Launch on this Mac

In Terminal:

```bash
cd /Users/abel_elreaper/Desktop/projects/Jetson-RealSense-Perception
python3 scripts/bench_dashboard.py
```

Then open [http://127.0.0.1:8765](http://127.0.0.1:8765). The server binds to
localhost by default, so it is not exposed to other computers on the network.
Stop it with `Control-C` in Terminal.

A convenience launcher named `Open Depth Bench Dashboard.command` is also on
the Desktop. Double-click it to start (or reuse) the localhost server and open
the dashboard. Its server log is written to `.bench_dashboard/server.log` in
this repository.

## Start point and controls

The checked-in `tests/fixtures/bench_synthetic.jsonl` fixture opens
automatically. It is visibly labeled synthetic and is not hardware validation.

- Choose **Load recording or report** for a local `.jsonl` recording or a
  `.json` report created by `scripts/replay_bench.py`.
- Use **Play/Pause**, **Step**, the timeline markers, or the range scrubber to
  move through events.
- The current policy state, nearest distance, valid-depth fraction, data age,
  and fault reason update at every event.
- PASS, FAIL, and SKIP are separate; SKIP never contributes to PASS.
- Malformed input appears in a red error panel with the line and column when
  available.

Files selected in the browser are processed only by the local server. Nothing
is uploaded to a cloud service.

## Offline replay and tests

```bash
cd /Users/abel_elreaper/Desktop/projects/Jetson-RealSense-Perception
python3 scripts/replay_bench.py tests/fixtures/bench_synthetic.jsonl
python3 -m unittest discover -s tests -v
```

To save a report that the dashboard can open later:

```bash
python3 scripts/replay_bench.py tests/fixtures/bench_synthetic.jsonl \
  --output /tmp/bench-report.json
```

## What is and is not verified

Verified on macOS without hardware: JSONL validation, policy transitions among
`CLEAR`, `STOP`, and `SENSOR_FAULT`, fault precedence, expected-result counts,
synthetic/hardware source labels, report generation, localhost API responses,
malformed-file errors, and browser timeline/transport behavior.

Still requires the repaired hardware: D455 recording quality, thresholds under
real lighting and surfaces, camera timestamps, RealSense/Jetson performance,
and physical safety validation. This dashboard is not live camera viewing,
SLAM, environment reconstruction, or a vehicle-control interface.

Future PX4 recording consumption, Omega1 rover-adapter consumption, and
RealmForge raw RGB-D/calibration support remain planned and are not implemented.
