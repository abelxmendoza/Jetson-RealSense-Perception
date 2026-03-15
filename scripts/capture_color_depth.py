#!/usr/bin/env python3
"""
Capture one color and one depth frame from RealSense and save as PNG files.
Useful for headless validation and CI. Requires no GUI.
"""
import argparse
import os
import sys

try:
    import pyrealsense2 as rs
    import numpy as np
    import cv2
except ImportError as e:
    print(f"Missing dependency: {e}", file=sys.stderr)
    sys.exit(1)


def parse_args():
    p = argparse.ArgumentParser(description="Capture color and depth frames to files")
    p.add_argument("--width", type=int, default=640, help="Color/depth width")
    p.add_argument("--height", type=int, default=480, help="Color/depth height")
    p.add_argument("--fps", type=int, default=30, help="Stream FPS")
    p.add_argument("-o", "--out-dir", default=".", help="Output directory (default: current)")
    p.add_argument("--color-name", default="color.png", help="Color output filename")
    p.add_argument("--depth-name", default="depth.png", help="Depth colormap output filename")
    return p.parse_args()


def main():
    args = parse_args()
    out_dir = os.path.abspath(args.out_dir)
    os.makedirs(out_dir, exist_ok=True)

    ctx = rs.context()
    devices = ctx.query_devices()
    if len(devices) == 0:
        print("No RealSense device found.", file=sys.stderr)
        return 1

    pipeline = rs.pipeline()
    config = rs.config()
    config.enable_stream(rs.stream.color, args.width, args.height, rs.format.bgr8, args.fps)
    config.enable_stream(rs.stream.depth, args.width, args.height, rs.format.z16, args.fps)

    try:
        pipeline.start(config)
    except RuntimeError as e:
        print(f"Failed to start camera: {e}", file=sys.stderr)
        print("Tip: Stop any other process using the camera (e.g. ROS node).", file=sys.stderr)
        return 1

    try:
        for _ in range(10):  # allow a few frames to stabilize
            frames = pipeline.wait_for_frames()
        color_frame = frames.get_color_frame()
        depth_frame = frames.get_depth_frame()
        if not color_frame or not depth_frame:
            print("Did not get color or depth frame.", file=sys.stderr)
            return 1

        color_image = np.asanyarray(color_frame.get_data())
        depth_image = np.asanyarray(depth_frame.get_data())

        color_path = os.path.join(out_dir, args.color_name)
        depth_path = os.path.join(out_dir, args.depth_name)

        cv2.imwrite(color_path, color_image)
        depth_colormap = cv2.applyColorMap(
            cv2.convertScaleAbs(depth_image, alpha=0.03),
            cv2.COLORMAP_JET
        )
        cv2.imwrite(depth_path, depth_colormap)

        print(f"Color: {color_path} ({color_image.shape[1]}x{color_image.shape[0]})")
        print(f"Depth: {depth_path} ({depth_image.shape[1]}x{depth_image.shape[0]})")
        return 0
    finally:
        pipeline.stop()


if __name__ == "__main__":
    sys.exit(main())
