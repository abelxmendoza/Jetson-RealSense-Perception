"""
Shared pipeline utilities for standalone pyrealsense2 scripts.
Provides device enumeration, pipeline creation, and retry-safe startup.
"""
import os
import sys
import time

import pyrealsense2 as rs


def find_device():
    """Enumerate RealSense devices and return the first one, or exit."""
    ctx = rs.context()
    devices = ctx.query_devices()
    if len(devices) == 0:
        print("No RealSense device found. Connect the camera and try again.")
        sys.exit(1)
    device = devices[0]
    print(f"Found RealSense device: {device.get_info(rs.camera_info.name)}")
    return device


def create_pipeline(color=True, depth=True, imu=False,
                    width=640, height=480, fps=30):
    """Create and configure a RealSense pipeline. Returns (pipeline, config)."""
    pipeline = rs.pipeline()
    config = rs.config()
    if color:
        config.enable_stream(rs.stream.color, width, height, rs.format.bgr8, fps)
    if depth:
        config.enable_stream(rs.stream.depth, width, height, rs.format.z16, fps)
    if imu:
        config.enable_stream(rs.stream.accel, rs.format.motion_xyz32f, 200)
        config.enable_stream(rs.stream.gyro, rs.format.motion_xyz32f, 200)
    return pipeline, config


def start_pipeline(pipeline, config, max_retries=3, retry_delay=2):
    """Start pipeline with retry logic for busy/errno=16 errors.

    Returns (pipeline, profile). The pipeline object may be recreated internally
    on retry, so always use the returned reference.
    """
    for attempt in range(max_retries):
        try:
            profile = pipeline.start(config)
            print("Camera started successfully!")
            return pipeline, profile
        except RuntimeError as e:
            msg = str(e).lower()
            if "busy" in msg or "errno=16" in msg:
                print(f"Camera busy (attempt {attempt + 1}/{max_retries})")
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                    try:
                        pipeline.stop()
                    except Exception:
                        pass
                    pipeline = rs.pipeline()
                else:
                    print(f"Error starting camera: {e}")
                    print("\nTroubleshooting:")
                    print("  1. Wait 5-10 seconds and try again")
                    print("  2. Unplug and replug the camera USB cable")
                    sys.exit(1)
            else:
                print(f"Error starting camera: {e}")
                sys.exit(1)


def add_no_gui_arg(parser):
    """Add standard --no-gui argument to an argparse parser."""
    parser.add_argument(
        "--no-gui", action="store_true",
        help="Run without OpenCV display windows (headless/SSH)"
    )


def resolve_gui(args):
    """Return True if GUI should be used (DISPLAY set and --no-gui not passed)."""
    return (not args.no_gui) and bool(os.environ.get("DISPLAY"))
