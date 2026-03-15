#!/usr/bin/env python3
"""
Print ROS2 topic list and type/hz for camera topics. Headless. Run with ROS2 sourced.
"""
import argparse
import sys
import subprocess


def main():
    p = argparse.ArgumentParser(description="List camera topics and optionally their hz")
    p.add_argument("--prefix", default="/camera", help="Topic prefix to filter")
    p.add_argument("--hz", action="store_true", help="Run ros2 topic hz on image topics")
    args = p.parse_args()

    try:
        out = subprocess.run(
            ["ros2", "topic", "list"],
            capture_output=True, text=True, timeout=5
        )
    except FileNotFoundError:
        print("ros2 not found. Source ROS2: source /opt/ros/humble/setup.bash", file=sys.stderr)
        return 1
    if out.returncode != 0:
        print(out.stderr or "ros2 topic list failed", file=sys.stderr)
        return 1

    topics = [t for t in out.stdout.strip().splitlines() if args.prefix in t]
    if not topics:
        print(f"No topics with prefix '{args.prefix}'. Is the RealSense node running?")
        return 0

    print("Topics:")
    for t in topics:
        print(f"  {t}")
    if args.hz:
        for t in topics:
            if "image" in t or "depth" in t:
                print(f"\nHz for {t}:")
                subprocess.run(["ros2", "topic", "hz", t], timeout=5)
    return 0


if __name__ == "__main__":
    sys.exit(main())
