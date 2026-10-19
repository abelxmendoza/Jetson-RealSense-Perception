"""Read and validate the portable JSONL bench recording format."""

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any, Iterable, Mapping, Optional


class RecordingError(ValueError):
    """A user-facing recording parse or validation error."""


@dataclass(frozen=True)
class BenchRecording:
    name: str
    source: str
    metadata: dict[str, Any]
    samples: list[dict[str, Any]]


def _number(record: Mapping[str, Any], aliases: Iterable[str], line_number: int) -> float:
    for key in aliases:
        if key in record:
            value = record[key]
            if isinstance(value, (int, float)) and not isinstance(value, bool):
                return float(value)
            raise RecordingError(f"line {line_number}: {key} must be a number")
    names = ", ".join(aliases)
    raise RecordingError(f"line {line_number}: missing required field ({names})")


def _normalize_sample(record: Mapping[str, Any], line_number: int, fallback_sequence: int) -> dict[str, Any]:
    expected = record.get("expected_status")
    if expected is not None and not isinstance(expected, str):
        raise RecordingError(f"line {line_number}: expected_status must be a string or null")
    fault = record.get("capture_fault_reason", record.get("fault_reason"))
    if fault is not None and not isinstance(fault, str):
        raise RecordingError(f"line {line_number}: capture_fault_reason must be a string or null")

    sequence = record.get("sequence", fallback_sequence)
    if not isinstance(sequence, int) or isinstance(sequence, bool) or sequence < 0:
        raise RecordingError(f"line {line_number}: sequence must be a non-negative integer")

    return {
        "sequence": sequence,
        "timestamp_s": _number(record, ("timestamp_s", "elapsed_s", "t"), line_number),
        "nearest_distance_m": _number(record, ("nearest_distance_m", "nearest_m"), line_number),
        "valid_depth_fraction": _number(
            record, ("valid_depth_fraction", "valid_fraction"), line_number
        ),
        "data_age_ms": _number(record, ("data_age_ms", "age_ms"), line_number),
        "capture_fault_reason": fault,
        "expected_status": expected,
    }


def parse_jsonl_text(text: str, name: str = "recording.jsonl") -> BenchRecording:
    metadata: dict[str, Any] = {}
    samples: list[dict[str, Any]] = []
    saw_content = False

    for line_number, raw_line in enumerate(text.splitlines(), start=1):
        stripped = raw_line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        saw_content = True
        try:
            record = json.loads(
                stripped,
                parse_constant=lambda value: (_ for _ in ()).throw(
                    ValueError(f"non-finite number {value} is not valid JSON")
                ),
            )
        except json.JSONDecodeError as exc:
            raise RecordingError(
                f"line {line_number}: malformed JSON at column {exc.colno}: {exc.msg}"
            ) from exc
        except ValueError as exc:
            raise RecordingError(f"line {line_number}: {exc}") from exc
        if not isinstance(record, dict):
            raise RecordingError(f"line {line_number}: each JSONL record must be an object")

        record_type = record.get("record_type", record.get("type", "sample"))
        if record_type == "metadata":
            if samples:
                raise RecordingError(f"line {line_number}: metadata must appear before samples")
            if metadata:
                raise RecordingError(f"line {line_number}: duplicate metadata record")
            if record.get("schema_version", 1) != 1:
                raise RecordingError(
                    f"line {line_number}: unsupported schema_version {record.get('schema_version')!r}"
                )
            metadata = dict(record)
        elif record_type == "sample":
            samples.append(_normalize_sample(record, line_number, len(samples)))
        else:
            raise RecordingError(f"line {line_number}: unsupported record_type {record_type!r}")

    if not saw_content:
        raise RecordingError("recording is empty")
    if not samples:
        raise RecordingError("recording contains no sample records")

    source = metadata.get("source", "unknown")
    if source not in {"synthetic", "hardware", "unknown"}:
        raise RecordingError("metadata source must be synthetic, hardware, or unknown")
    return BenchRecording(name=name, source=source, metadata=metadata, samples=samples)


def load_jsonl(path: str | Path) -> BenchRecording:
    recording_path = Path(path)
    try:
        text = recording_path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        raise RecordingError(f"could not read {recording_path}: {exc}") from exc
    return parse_jsonl_text(text, recording_path.name)
