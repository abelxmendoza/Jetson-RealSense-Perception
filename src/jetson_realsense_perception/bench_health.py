"""Deterministic health policy for recorded depth-perception samples.

This module intentionally has no ROS, RealSense, or third-party dependencies so
recordings can be evaluated on a developer laptop.
"""

from dataclasses import asdict, dataclass
import math
from typing import Any, Mapping, Optional


CLEAR = "CLEAR"
STOP = "STOP"
SENSOR_FAULT = "SENSOR_FAULT"
VALID_STATUSES = {CLEAR, STOP, SENSOR_FAULT}


@dataclass(frozen=True)
class BenchPolicy:
    stop_distance_m: float = 1.0
    min_valid_depth_fraction: float = 0.50
    max_data_age_ms: float = 500.0

    def __post_init__(self) -> None:
        if not _finite_number(self.stop_distance_m) or self.stop_distance_m <= 0:
            raise ValueError("stop_distance_m must be a positive finite number")
        if not _finite_number(self.min_valid_depth_fraction) or not 0 <= self.min_valid_depth_fraction <= 1:
            raise ValueError("min_valid_depth_fraction must be between 0 and 1")
        if not _finite_number(self.max_data_age_ms) or self.max_data_age_ms < 0:
            raise ValueError("max_data_age_ms must be a non-negative finite number")

    def to_dict(self) -> dict[str, float]:
        return asdict(self)


@dataclass(frozen=True)
class HealthEvaluation:
    status: str
    fault_reason: Optional[str]

    def to_dict(self) -> dict[str, Optional[str]]:
        return asdict(self)


def _finite_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def evaluate_sample(sample: Mapping[str, Any], policy: BenchPolicy = BenchPolicy()) -> HealthEvaluation:
    """Evaluate one normalized sample, with sensor faults taking precedence."""
    capture_fault = sample.get("capture_fault_reason")
    if capture_fault:
        return HealthEvaluation(SENSOR_FAULT, str(capture_fault))

    age = sample.get("data_age_ms")
    if not _finite_number(age) or age < 0:
        return HealthEvaluation(SENSOR_FAULT, "data age is missing or invalid")
    if age > policy.max_data_age_ms:
        return HealthEvaluation(
            SENSOR_FAULT,
            f"stale depth data ({age:.0f} ms > {policy.max_data_age_ms:.0f} ms)",
        )

    valid_fraction = sample.get("valid_depth_fraction")
    if not _finite_number(valid_fraction) or not 0 <= valid_fraction <= 1:
        return HealthEvaluation(SENSOR_FAULT, "valid-depth fraction is missing or invalid")
    if valid_fraction < policy.min_valid_depth_fraction:
        return HealthEvaluation(
            SENSOR_FAULT,
            "insufficient valid depth "
            f"({valid_fraction:.1%} < {policy.min_valid_depth_fraction:.1%})",
        )

    nearest = sample.get("nearest_distance_m")
    if not _finite_number(nearest) or nearest <= 0:
        return HealthEvaluation(SENSOR_FAULT, "nearest distance is missing or invalid")
    if nearest <= policy.stop_distance_m:
        return HealthEvaluation(STOP, None)
    return HealthEvaluation(CLEAR, None)


def comparison_outcome(expected_status: Any, actual_status: str) -> str:
    """Return PASS, FAIL, or SKIP; absent expectations are never counted as PASS."""
    if expected_status is None or expected_status == "":
        return "SKIP"
    if expected_status not in VALID_STATUSES:
        return "FAIL"
    return "PASS" if expected_status == actual_status else "FAIL"
