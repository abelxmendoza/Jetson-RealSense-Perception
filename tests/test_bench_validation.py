import sys
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from jetson_realsense_perception.bench_recording import RecordingError, parse_jsonl_text

SAMPLE = '{"timestamp_s":0,"nearest_distance_m":2,"valid_depth_fraction":0.9,"data_age_ms":1}'

class ValidationTests(unittest.TestCase):
    def test_overflow_is_rejected_in_every_metric(self):
        import json
        for key in ('timestamp_s', 'nearest_distance_m', 'valid_depth_fraction', 'data_age_ms'):
            value = json.loads(SAMPLE)
            value[key] = 'OVERFLOW'
            with self.subTest(key=key), self.assertRaisesRegex(RecordingError, 'finite'):
                parse_jsonl_text(json.dumps(value).replace('"OVERFLOW"', '1e999'))

    def test_non_string_source_is_user_error(self):
        for source in ('[]', '{}', 'null', '3'):
            with self.subTest(source=source), self.assertRaisesRegex(RecordingError, 'metadata source'):
                parse_jsonl_text('{"record_type":"metadata","source":' + source + '}\n' + SAMPLE)


class FrameAgeTests(unittest.TestCase):
    def test_frame_age_uses_capture_timestamp(self):
        from types import SimpleNamespace
        sys.path.insert(0, str(ROOT / 'scripts'))
        from bench_depth_monitor import frame_age_ms
        rs = SimpleNamespace(timestamp_domain=SimpleNamespace(system_time=1, global_time=2))
        self.assertEqual(frame_age_ms(1000, 2, rs, 1800), (800, None))
        self.assertEqual(frame_age_ms(1000, 1, rs, 1020), (20, None))
        for timestamp, domain in ((1000, 3), (2000, 2), (float('nan'), 2)):
            with self.subTest(timestamp=timestamp, domain=domain):
                age, fault = frame_age_ms(timestamp, domain, rs, 1800)
                self.assertIsNotNone(fault)
                self.assertEqual(age, 0)
