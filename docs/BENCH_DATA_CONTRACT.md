# Bench data contract

The bench tools use newline-delimited JSON (JSONL) so recordings remain easy to
inspect, stream, diff, and replay without ROS or RealSense libraries.

## Recording format

Blank lines and lines beginning with `#` are ignored. Each remaining line must
be one JSON object. A recording may begin with one metadata record:

```json
{"record_type":"metadata","schema_version":1,"source":"synthetic","name":"Example"}
```

`source` must be `synthetic`, `hardware`, or `unknown`. This label is carried
into generated reports and displayed prominently by the dashboard. A synthetic
recording is never presented as hardware validation.

Sample records follow:

```json
{"record_type":"sample","sequence":0,"timestamp_s":0.0,"nearest_distance_m":1.42,"valid_depth_fraction":0.91,"data_age_ms":24,"expected_status":"CLEAR"}
```

Required numeric fields:

| Field | Meaning |
| --- | --- |
| `timestamp_s` | Seconds from the start of this recording |
| `nearest_distance_m` | Nearest usable depth in metres |
| `valid_depth_fraction` | Fraction of depth pixels that are valid, from 0 to 1 |
| `data_age_ms` | Age of the sample in milliseconds |

Optional fields:

| Field | Meaning |
| --- | --- |
| `sequence` | Source sequence number; defaults to the zero-based row index |
| `capture_fault_reason` | Upstream capture error; forces `SENSOR_FAULT` |
| `expected_status` | `CLEAR`, `STOP`, `SENSOR_FAULT`, or `null` |

For compatibility, the reader also accepts `elapsed_s` or `t`, `nearest_m`,
`valid_fraction`, and `age_ms` as aliases. New recordings should use the
canonical names above.

## Default replay policy

`scripts/replay_bench.py` and
`src/jetson_realsense_perception/bench_health.py` are the source of truth:

1. Missing/invalid metrics, a capture fault, data older than 500 ms, or valid
   depth below 50% yields `SENSOR_FAULT`.
2. Otherwise, a nearest distance at or below 1.0 m yields `STOP`.
3. Otherwise the result is `CLEAR`.

Sensor faults take precedence over obstacle distance. Thresholds can be changed
with replay CLI flags, but the dashboard API intentionally uses the defaults.

## Expected-result counts

- `PASS`: an expected status exists and matches the evaluated status.
- `FAIL`: an expected status exists and does not match (or is not recognized).
- `SKIP`: no expected status was supplied.

`SKIP` is reported separately and is never treated as `PASS`.

## Replay report

Generate a portable JSON report:

```bash
python3 scripts/replay_bench.py tests/fixtures/bench_synthetic.jsonl \
  --output /tmp/bench-report.json
```

The report contains `recording`, `policy`, `summary`, and evaluated `events`.
The dashboard can open either a raw `.jsonl` recording or this generated `.json`
report. Raw JSONL is sent only to the localhost Python process, where the same
replay implementation evaluates it.

## Scope

This contract describes compact health summaries, not raw RGB-D frames or
camera calibration. Future PX4 replay, an Omega1 rover adapter, and RealmForge
raw RGB-D/calibration ingestion are planned integrations and are not implemented
by this dashboard.
