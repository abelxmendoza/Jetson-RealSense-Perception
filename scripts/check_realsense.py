#!/usr/bin/env python3
"""
Verify pyrealsense2 and enumerate connected RealSense devices.
Exits with nonzero status if no camera is found. Use after SDK install to validate setup.
"""
import sys

def main():
    try:
        import pyrealsense2 as rs
    except ImportError:
        print("ERROR: pyrealsense2 not found. Install RealSense SDK 2.0 (librealsense) first.", file=sys.stderr)
        return 1

    ctx = rs.context()
    devices = ctx.query_devices()
    if len(devices) == 0:
        print("ERROR: No RealSense device found. Connect a camera and try again.", file=sys.stderr)
        return 1

    for i, dev in enumerate(devices):
        name = dev.get_info(rs.camera_info.name)
        serial = dev.get_info(rs.camera_info.serial_number)
        fw = dev.get_info(rs.camera_info.firmware_version)
        usb = dev.get_info(rs.camera_info.usb_type_descriptor) if hasattr(rs.camera_info, 'usb_type_descriptor') else "N/A"
        print(f"Device {i}: {name}")
        print(f"  Serial: {serial}")
        print(f"  Firmware: {fw}")
        print(f"  USB: {usb}")

    print("OK: RealSense device(s) found.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
