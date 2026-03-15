#!/usr/bin/env python3
"""ROS2 RealSense topic report tool.

Checks if expected realsense2_camera topics exist and optionally samples one camera_info message.
"""

import argparse
import subprocess
import sys

EXPECTED_TOPICS = [
    "/camera/camera/color/image_raw",
    "/camera/camera/color/camera_info",
    "/camera/camera/depth/image_rect_raw",
    "/camera/camera/depth/camera_info",
    "/camera/camera/extrinsics/depth_to_color",
]


def run_ros2_topic_list():
    try:
        output = subprocess.check_output(["ros2", "topic", "list"], stderr=subprocess.STDOUT, text=True)
        return output.splitlines()
    except subprocess.CalledProcessError as e:
        print("ERROR: Failed to run 'ros2 topic list'. Is ROS2 sourced?", file=sys.stderr)
        print(e.output, file=sys.stderr)
        sys.exit(2)


def sample_topic(topic):
    try:
        sample = subprocess.check_output(["ros2", "topic", "echo", topic, "--once"], stderr=subprocess.STDOUT, text=True, timeout=10)
        return sample
    except subprocess.CalledProcessError as e:
        return None
    except subprocess.TimeoutExpired:
        return None


def main():
    parser = argparse.ArgumentParser(description="Validate required RealSense ROS2 topics.")
    parser.add_argument("--sample", action="store_true", help="Sample one message from camera_info topics")
    args = parser.parse_args()

    print("ROS2 RealSense topic report")
    print("============================")

    available = set(run_ros2_topic_list())

    missing = []
    for topic in EXPECTED_TOPICS:
        status = "OK" if topic in available else "MISSING"
        print(f"{status}: {topic}")
        if status != "OK":
            missing.append(topic)

    print("\nSummary:")
    print(f"  available: {len([t for t in EXPECTED_TOPICS if t in available])}/{len(EXPECTED_TOPICS)}")
    if missing:
        print("  missing:")
        for t in missing:
            print(f"    - {t}")

    if args.sample:
        print("\nSampling camera_info messages from topics")
        for topic in ["/camera/camera/color/camera_info", "/camera/camera/depth/camera_info"]:
            if topic not in available:
                print(f"  skip: {topic} not found")
                continue
            print(f"  sampling: {topic}")
            sample = sample_topic(topic)
            if sample:
                print("    sample success (first few lines):")
                for line in sample.splitlines()[:5]:
                    print("      ", line)
            else:
                print("    sample failed or timed out")

    if missing:
        sys.exit(1)
    print("All required topics present.")
    sys.exit(0)


if __name__ == "__main__":
    main()
