"""Hardware-independent depth frames and local obstacle observations.

Optical coordinates: x right, y down, z forward. Depth is axial z in metres.
No robot control, world localization, or persistent mapping is performed here.
"""
from dataclasses import dataclass
import math
import numpy as np
from .bench_health import evaluate_sample


@dataclass(frozen=True)
class CameraModel:
    width: int = 160
    height: int = 120
    fx: float = 140.0
    fy: float = 140.0
    cx: float = 79.5
    cy: float = 59.5

    def __post_init__(self):
        if self.width < 3 or self.height < 3:
            raise ValueError('image must be at least 3 by 3')
        if not all(math.isfinite(v) for v in (self.fx, self.fy, self.cx, self.cy)) or min(self.fx, self.fy) <= 0:
            raise ValueError('intrinsics must be finite with positive focal lengths')


@dataclass
class DepthFrame:
    depth_m: np.ndarray
    camera: CameraModel
    timestamp_s: float
    source: str
    frame_id: str = 'camera_optical_frame'
    capture_fault_reason: str | None = None


def rays(camera):
    v, u = np.indices((camera.height, camera.width))
    return np.stack(((u-camera.cx)/camera.fx, (v-camera.cy)/camera.fy, np.ones_like(u)), axis=-1)


def point_cloud(frame):
    if frame.depth_m.shape != (frame.camera.height, frame.camera.width):
        raise ValueError('depth shape does not match calibration')
    valid = np.isfinite(frame.depth_m) & (frame.depth_m > 0)
    return (rays(frame.camera) * frame.depth_m[..., None])[valid]


class SimulatedCamera:
    """Pinhole ray intersections with room planes and a moving cuboid."""
    def __init__(self, camera=CameraModel(), seed=7):
        self.camera = camera
        self.rng = np.random.default_rng(seed)
        self.last = None

    def capture(self, timestamp_s, distance_m=2.0, fault='none'):
        if fault == 'frozen' and self.last is not None:
            return self.last
        direction = rays(self.camera)
        depth = np.full(direction.shape[:2], 6.0)  # rear wall
        # Camera at 1 m height, walls at +/-2 m, ceiling at 2.5 m.
        for axis, plane in ((0, -2.), (0, 2.), (1, 1.), (1, -1.5)):
            hit = np.divide(plane, direction[..., axis], out=np.full(depth.shape, np.inf), where=direction[..., axis] != 0)
            depth = np.minimum(depth, np.where(hit > 0, hit, np.inf))
        # Axis-aligned cuboid, front surface at distance_m.
        near = np.full(depth.shape, -np.inf)
        far = np.full(depth.shape, np.inf)
        for axis, lo, hi in ((0, -.35, .35), (1, -.45, .45), (2, distance_m, distance_m+.5)):
            d = direction[..., axis]
            a = np.divide(lo, d, out=np.full(depth.shape, -np.inf), where=d != 0)
            b = np.divide(hi, d, out=np.full(depth.shape, np.inf), where=d != 0)
            near = np.maximum(near, np.minimum(a, b))
            far = np.minimum(far, np.maximum(a, b))
        depth = np.minimum(depth, np.where((far >= near) & (near > 0), near, np.inf))
        if fault == 'dropout':
            depth[self.rng.random(depth.shape) < .85] = 0
        elif fault == 'disconnect':
            depth[:] = 0
        frame = DepthFrame(depth.astype(np.float32), self.camera, timestamp_s, 'synthetic',
                           capture_fault_reason='simulated camera disconnected' if fault == 'disconnect' else None)
        self.last = frame
        return frame


def process_depth(frame, now_s):
    """Evaluate a central forward ROI; return portable metrics and local points."""
    points = point_cloud(frame)
    h, w = frame.depth_m.shape
    roi = frame.depth_m[h//3:2*h//3, w//3:2*w//3]
    valid = np.isfinite(roi) & (roi > 0)
    age = (now_s-frame.timestamp_s)*1000
    sample = {
        'timestamp_s': frame.timestamp_s,
        'nearest_distance_m': float(roi[valid].min()) if valid.any() else 0.,
        'valid_depth_fraction': float(valid.mean()),
        'data_age_ms': age,
        'capture_fault_reason': frame.capture_fault_reason,
        'expected_status': None,
    }
    evaluation = evaluate_sample(sample)
    # Remove floor/ceiling by height band; this is a camera-relative local map.
    obstacles = points[(points[:, 1] > -.8) & (points[:, 1] < .8)]
    return sample, evaluation, obstacles
