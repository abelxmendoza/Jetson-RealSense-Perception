#!/usr/bin/env python3
"""RealSense obstacle detector (zone-based) for Jetson RealSense perception sandbox."""

import argparse
import sys
import time

import cv2
import numpy as np
import pyrealsense2 as rs


def create_pipeline(fps=30):
    pipeline = rs.pipeline()
    config = rs.config()
    config.enable_stream(rs.stream.color, 640, 480, rs.format.bgr8, fps)
    config.enable_stream(rs.stream.depth, 640, 480, rs.format.z16, fps)
    return pipeline, config


def parse_args():
    parser = argparse.ArgumentParser(description='RealSense obstacle detector')
    parser.add_argument('--min-distance', type=float, default=0.5,
                        help='Obstacle threshold distance in meters (default: 0.5)')
    parser.add_argument('--roi', type=float, nargs=2, default=[0.33, 0.33],
                        metavar=('WIDTH', 'HEIGHT'),
                        help='ROI width/height as fraction of image dimensions (default: 0.33 0.33)')
    parser.add_argument('--fps', type=int, default=30,
                        help='Camera stream framerate (default: 30)')
    args = parser.parse_args()

    if not 0 < args.roi[0] <= 1 or not 0 < args.roi[1] <= 1:
        parser.error('ROI dimensions must be >0 and <=1')

    return args


def main():
    args = parse_args()

    print('Starting obstacle_detector with args:', args)

    # Detect device and print info
    ctx = rs.context()
    devices = ctx.query_devices()
    if len(devices) == 0:
        print('No RealSense device found. Connect the camera and try again.')
        sys.exit(1)
    print('Found RealSense device:', devices[0].get_info(rs.camera_info.name))

    pipeline, config = create_pipeline(fps=args.fps)

    # Boot camera with retry-friendly behavior
    max_retries = 3
    retry_delay = 2
    for attempt in range(max_retries):
        try:
            pipeline.start(config)
            print('Camera started successfully!')
            break
        except RuntimeError as e:
            msg = str(e).lower()
            if 'busy' in msg or 'errno=16' in msg:
                print(f'Camera busy (attempt {attempt+1}/{max_retries})')
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                    try:
                        pipeline.stop()
                    except Exception:
                        pass
                    pipeline = rs.pipeline()
                else:
                    raise
            else:
                raise

    try:
        while True:
            frames = pipeline.wait_for_frames()
            depth_frame = frames.get_depth_frame()
            color_frame = frames.get_color_frame()

            if not depth_frame or not color_frame:
                continue

            depth_image = np.asanyarray(depth_frame.get_data())
            color_image = np.asanyarray(color_frame.get_data())

            h, w = depth_image.shape
            roi_w = int(w * args.roi[0])
            roi_h = int(h * args.roi[1])
            x1 = (w - roi_w) // 2
            y1 = (h - roi_h) // 2
            x2 = x1 + roi_w
            y2 = y1 + roi_h

            center_region = depth_image[y1:y2, x1:x2]
            valid_depths = center_region[(center_region > 0) & (center_region < 10000)]

            if len(valid_depths) > 0:
                # Convert mm to meters (RealSense z16 is in mm)
                dists = valid_depths.astype(np.float32) / 1000.0
                median_distance = float(np.median(dists))
                min_distance = float(np.min(dists))
            else:
                median_distance = 10.0
                min_distance = 10.0

            if median_distance < args.min_distance or min_distance < args.min_distance:
                status = 'OBSTACLE'
                color = (0, 0, 255)
                cv2.rectangle(color_image, (x1, y1), (x2, y2), (0, 0, 255), 3)
            else:
                status = 'CLEAR'
                color = (0, 255, 0)
                cv2.rectangle(color_image, (x1, y1), (x2, y2), (255, 255, 0), 1)

            text = f'{status}: median={median_distance:.2f}m min={min_distance:.2f}m (th={args.min_distance:.2f}m)'
            cv2.putText(color_image, text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)

            cv2.imshow('Navigation View', color_image)

            key = cv2.waitKey(1) & 0xFF
            if key == ord('q') or key == 27:
                break

    except KeyboardInterrupt:
        print('Interrupted by user')

    finally:
        pipeline.stop()
        cv2.destroyAllWindows()
        print('Exited safely')


if __name__ == '__main__':
    main()
