#!/usr/bin/env python3
"""
Print RealSense device and stream info (profiles, fps). Uses pyrealsense2 only.
Useful to verify camera after SDK install and before running other scripts.
"""
import sys

try:
    import pyrealsense2 as rs
except ImportError:
    print("pyrealsense2 not found. Install RealSense SDK 2.0 (librealsense) first.", file=sys.stderr)
    sys.exit(1)


def main():
    ctx = rs.context()
    devices = ctx.query_devices()
    if len(devices) == 0:
        print("No RealSense device found.")
        sys.exit(1)

    dev = devices[0]
    print("Device:", dev.get_info(rs.camera_info.name))
    print("Serial:", dev.get_info(rs.camera_info.serial_number))
    print("Firmware:", dev.get_info(rs.camera_info.firmware_version))

    for sensor in dev.query_sensors():
        print("\nSensor:", sensor.get_info(rs.camera_info.name))
        for profile in sensor.get_stream_profiles():
            if profile.is_video_stream_profile():
                vp = profile.as_video_stream_profile()
                print(f"  {vp.stream_type()} {vp.width()}x{vp.height()} @ {vp.fps()} fps")
            else:
                print(f"  {profile.stream_type()} @ {profile.fps()} fps")

    print("\nDone.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
