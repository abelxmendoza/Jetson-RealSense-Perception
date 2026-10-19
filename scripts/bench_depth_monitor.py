#!/usr/bin/env python3
"""Record a simple RealSense depth-health JSONL stream for later replay.

The import is intentionally deferred: this file remains inspectable on a Mac
without pyrealsense2, but hardware recording requires the RealSense SDK.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import signal
import time


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", help="new JSONL recording path")
    parser.add_argument("--duration", type=float, default=30.0, help="seconds to record")
    parser.add_argument("--fps", type=int, default=15)
    args = parser.parse_args()

    output = Path(args.output)
    if output.exists():
        parser.error(f"refusing to overwrite existing file: {output}")
    try:
        import numpy as np
        import pyrealsense2 as rs
    except ImportError as exc:
        parser.error(f"hardware recording requires numpy and pyrealsense2: {exc}")

    pipeline = rs.pipeline()
    config = rs.config()
    config.enable_stream(rs.stream.depth, 640, 480, rs.format.z16, args.fps)
    profile = pipeline.start(config)
    depth_scale = profile.get_device().first_depth_sensor().get_depth_scale()
    stop = False

    def request_stop(_signum, _frame):
        nonlocal stop
        stop = True

    signal.signal(signal.SIGINT, request_stop)
    started = time.monotonic()
    output.parent.mkdir(parents=True, exist_ok=True)
    try:
        with output.open("x", encoding="utf-8") as handle:
            metadata = {
                "record_type": "metadata",
                "schema_version": 1,
                "source": "hardware",
                "camera": "Intel RealSense",
                "recorded_at": datetime.now(timezone.utc).isoformat(),
            }
            handle.write(json.dumps(metadata) + "\n")
            sequence = 0
            while not stop and time.monotonic() - started < args.duration:
                wait_started = time.monotonic()
                frames = pipeline.wait_for_frames(timeout_ms=2000)
                depth = frames.get_depth_frame()
                age_ms = (time.monotonic() - wait_started) * 1000.0
                values = np.asanyarray(depth.get_data())
                valid = values > 0
                valid_values = values[valid]
                nearest = float(np.percentile(valid_values, 5) * depth_scale) if valid_values.size else 0.0
                sample = {
                    "record_type": "sample",
                    "sequence": sequence,
                    "timestamp_s": round(time.monotonic() - started, 6),
                    "nearest_distance_m": nearest,
                    "valid_depth_fraction": float(valid.mean()),
                    "data_age_ms": age_ms,
                    "expected_status": None,
                }
                handle.write(json.dumps(sample) + "\n")
                handle.flush()
                sequence += 1
    finally:
        pipeline.stop()
    print(f"recorded {sequence} samples to {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
