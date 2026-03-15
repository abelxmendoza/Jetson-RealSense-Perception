#!/usr/bin/env python3
"""
Echo one camera_info message from color and depth. Headless. Run with ROS2 sourced.
Useful to verify intrinsics are published correctly.
"""
import argparse
import sys
import subprocess


def main():
    p = argparse.ArgumentParser(description="Echo one camera_info from color and depth topics")
    p.add_argument("--color-topic", default="/camera/camera/color/camera_info")
    p.add_argument("--depth-topic", default="/camera/camera/depth/camera_info")
    args = p.parse_args()

    try:
        subprocess.run(["ros2", "topic", "echo", args.color_topic, "--once"], timeout=10)
    except FileNotFoundError:
        print("ros2 not found. Source ROS2 first.", file=sys.stderr)
        return 1
    except subprocess.TimeoutExpired:
        print(f"Timeout waiting for {args.color_topic}", file=sys.stderr)

    print("\n--- Depth camera_info ---\n")
    try:
        subprocess.run(["ros2", "topic", "echo", args.depth_topic, "--once"], timeout=10)
    except subprocess.TimeoutExpired:
        print(f"Timeout waiting for {args.depth_topic}", file=sys.stderr)

    return 0


if __name__ == "__main__":
    sys.exit(main())
