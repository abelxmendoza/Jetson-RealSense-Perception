#!/usr/bin/env python3
"""Replay a depth bench recording through the authoritative health policy."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from jetson_realsense_perception.bench_health import (  # noqa: E402
    BenchPolicy,
    comparison_outcome,
    evaluate_sample,
)
from jetson_realsense_perception.bench_recording import (  # noqa: E402
    BenchRecording,
    RecordingError,
    load_jsonl,
)


def build_report(recording: BenchRecording, policy: BenchPolicy = BenchPolicy()) -> dict[str, Any]:
    events: list[dict[str, Any]] = []
    counts = {"PASS": 0, "FAIL": 0, "SKIP": 0}
    status_counts = {"CLEAR": 0, "STOP": 0, "SENSOR_FAULT": 0}

    for sample in recording.samples:
        evaluation = evaluate_sample(sample, policy)
        outcome = comparison_outcome(sample.get("expected_status"), evaluation.status)
        counts[outcome] += 1
        status_counts[evaluation.status] += 1
        events.append(
            {
                **sample,
                "status": evaluation.status,
                "fault_reason": evaluation.fault_reason,
                "outcome": outcome,
            }
        )

    return {
        "report_type": "bench_replay_report",
        "schema_version": 1,
        "recording": {
            "name": recording.name,
            "source": recording.source,
            "source_label": {
                "synthetic": "Synthetic fixture — not hardware validation",
                "hardware": "Hardware-recorded data",
                "unknown": "Unknown recording source",
            }[recording.source],
            "metadata": recording.metadata,
        },
        "policy": policy.to_dict(),
        "summary": {"outcomes": counts, "statuses": status_counts, "total": len(events)},
        "events": events,
    }


def create_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("recording", help="path to a bench JSONL recording")
    parser.add_argument("--output", "-o", help="write the replay report to this JSON file")
    parser.add_argument("--stop-distance-m", type=float, default=1.0)
    parser.add_argument("--min-valid-depth-fraction", type=float, default=0.50)
    parser.add_argument("--max-data-age-ms", type=float, default=500.0)
    return parser


def main() -> int:
    args = create_parser().parse_args()
    policy = BenchPolicy(
        stop_distance_m=args.stop_distance_m,
        min_valid_depth_fraction=args.min_valid_depth_fraction,
        max_data_age_ms=args.max_data_age_ms,
    )
    try:
        report = build_report(load_jsonl(args.recording), policy)
    except RecordingError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    rendered = json.dumps(report, indent=2, sort_keys=True)
    if args.output:
        Path(args.output).write_text(rendered + "\n", encoding="utf-8")
    else:
        print(rendered)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
