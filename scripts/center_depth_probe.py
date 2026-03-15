#!/usr/bin/env python3
"""
Stream depth and print center-pixel distance (or custom x,y). No GUI required.
Valid readings depend on scene content and exclusive camera access (no ROS node holding the device).
"""
import argparse
import sys
import time

try:
    import pyrealsense2 as rs
except ImportError:
    print("pyrealsense2 not found. Install RealSense SDK 2.0 first.", file=sys.stderr)
    sys.exit(1)


def parse_args():
    p = argparse.ArgumentParser(description="Print depth at center pixel (or x,y)")
    p.add_argument("--x", type=int, default=None, help="Pixel x (default: center)")
    p.add_argument("--y", type=int, default=None, help="Pixel y (default: center)")
    p.add_argument("--count", type=int, default=0, help="Number of readings (0 = infinite)")
    p.add_argument("--interval", type=float, default=0.5, help="Seconds between readings")
    return p.parse_args()


def main():
    args = parse_args()

    ctx = rs.context()
    devices = ctx.query_devices()
    if len(devices) == 0:
        print("No RealSense device found.", file=sys.stderr)
        return 1

    pipeline = rs.pipeline()
    config = rs.config()
    config.enable_stream(rs.stream.depth, 640, 480, rs.format.z16, 30)

    try:
        pipeline.start(config)
    except RuntimeError as e:
        print(f"Failed to start: {e}", file=sys.stderr)
        return 1

    n = 0
    try:
        while args.count == 0 or n < args.count:
            frames = pipeline.wait_for_frames()
            depth_frame = frames.get_depth_frame()
            if not depth_frame:
                continue
            w = depth_frame.get_width()
            h = depth_frame.get_height()
            cx = args.x if args.x is not None else w // 2
            cy = args.y if args.y is not None else h // 2
            if not (0 <= cx < w and 0 <= cy < h):
                print(f"Invalid pixel ({cx},{cy}) for {w}x{h}", file=sys.stderr)
                break
            dist = depth_frame.get_distance(cx, cy)
            print(f"({cx},{cy}): {dist:.3f} m")
            n += 1
            if args.count == 0 or n < args.count:
                time.sleep(args.interval)
    except KeyboardInterrupt:
        pass
    finally:
        pipeline.stop()

    return 0


if __name__ == "__main__":
    sys.exit(main())
