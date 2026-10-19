import json
from pathlib import Path
import subprocess
import sys
import unittest

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from jetson_realsense_perception.bench_health import BenchPolicy, evaluate_sample
from jetson_realsense_perception.bench_recording import RecordingError, load_jsonl, parse_jsonl_text
from replay_bench import build_report


class HealthPolicyTests(unittest.TestCase):
    def test_clear_stop_and_fault_precedence(self):
        base = {"nearest_distance_m": 2.0, "valid_depth_fraction": 0.9, "data_age_ms": 20}
        self.assertEqual(evaluate_sample(base).status, "CLEAR")
        self.assertEqual(evaluate_sample({**base, "nearest_distance_m": 0.8}).status, "STOP")
        fault = evaluate_sample({**base, "nearest_distance_m": 0.8, "data_age_ms": 900})
        self.assertEqual(fault.status, "SENSOR_FAULT")
        self.assertIn("stale", fault.fault_reason)

    def test_thresholds_are_inclusive(self):
        sample = {"nearest_distance_m": 1.0, "valid_depth_fraction": 0.5, "data_age_ms": 500}
        self.assertEqual(evaluate_sample(sample, BenchPolicy()).status, "STOP")


class RecordingTests(unittest.TestCase):
    def test_fixture_transitions_labels_and_counts(self):
        report = build_report(load_jsonl(REPO_ROOT / "tests/fixtures/bench_synthetic.jsonl"))
        self.assertEqual(report["recording"]["source"], "synthetic")
        self.assertIn("not hardware validation", report["recording"]["source_label"])
        self.assertEqual(report["summary"]["outcomes"], {"PASS": 9, "FAIL": 0, "SKIP": 1})
        self.assertEqual(
            {event["status"] for event in report["events"]},
            {"CLEAR", "STOP", "SENSOR_FAULT"},
        )

    def test_hardware_label(self):
        text = '\n'.join([
            '{"record_type":"metadata","source":"hardware"}',
            '{"timestamp_s":0,"nearest_distance_m":2,"valid_depth_fraction":0.9,"data_age_ms":1}',
        ])
        report = build_report(parse_jsonl_text(text, "hardware.jsonl"))
        self.assertEqual(report["recording"]["source_label"], "Hardware-recorded data")
        self.assertEqual(report["summary"]["outcomes"]["SKIP"], 1)
        self.assertEqual(report["summary"]["outcomes"]["PASS"], 0)

    def test_malformed_json_has_line_and_column(self):
        with self.assertRaisesRegex(RecordingError, r"line 2: malformed JSON at column"):
            parse_jsonl_text('{"record_type":"metadata"}\n{"bad":')

    def test_cli_report(self):
        result = subprocess.run(
            [sys.executable, str(REPO_ROOT / "scripts/replay_bench.py"), str(REPO_ROOT / "tests/fixtures/bench_synthetic.jsonl")],
            check=True,
            capture_output=True,
            text=True,
        )
        self.assertEqual(json.loads(result.stdout)["report_type"], "bench_replay_report")


if __name__ == "__main__":
    unittest.main()
