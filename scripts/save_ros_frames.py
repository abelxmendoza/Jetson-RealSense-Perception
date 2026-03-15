#!/usr/bin/env python3
"""
Subscribe to RealSense color and depth topics, save one frame of each to files.
Uses rclpy and cv_bridge. Works headless (no GUI). Run with ROS2 sourced and
realsense2_camera node running.
"""
import argparse
import sys
import os

try:
    import rclpy
    from rclpy.node import Node
    from sensor_msgs.msg import Image
    from cv_bridge import CvBridge
    import cv2
except ImportError as e:
    print(f"Missing dependency: {e}", file=sys.stderr)
    print("Need: ROS2 Humble (rclpy), cv_bridge, opencv-python. Source your workspace.", file=sys.stderr)
    sys.exit(1)


class FrameSaver(Node):
    def __init__(self, color_topic, depth_topic, out_dir):
        super().__init__("save_ros_frames")
        self.bridge = CvBridge()
        self.out_dir = os.path.abspath(out_dir)
        os.makedirs(self.out_dir, exist_ok=True)
        self.color_received = None
        self.depth_received = None
        self.color_ts = None
        self.depth_ts = None

        self.sub_color = self.create_subscription(
            Image, color_topic, self.color_cb, 10
        )
        self.sub_depth = self.create_subscription(
            Image, depth_topic, self.depth_cb, 10
        )

    def color_cb(self, msg):
        if self.color_received is None:
            self.color_received = self.bridge.imgmsg_to_cv2(msg, desired_encoding="bgr8")
            self.color_ts = msg.header.stamp

    def depth_cb(self, msg):
        if self.depth_received is None:
            self.depth_received = self.bridge.imgmsg_to_cv2(msg, desired_encoding="passthrough")
            self.depth_ts = msg.header.stamp


def main():
    p = argparse.ArgumentParser(description="Save one color and one depth frame from ROS2 topics")
    p.add_argument("--color-topic", default="/camera/camera/color/image_raw")
    p.add_argument("--depth-topic", default="/camera/camera/depth/image_rect_raw")
    p.add_argument("-o", "--out-dir", default=".")
    p.add_argument("--timeout", type=float, default=15.0, help="Seconds to wait for both frames")
    args = p.parse_args()

    rclpy.init()
    node = FrameSaver(args.color_topic, args.depth_topic, args.out_dir)

    import time
    start = time.time()
    while rclpy.ok() and time.time() - start < args.timeout:
        rclpy.spin_once(node, timeout_sec=0.2)
        if node.color_received is not None and node.depth_received is not None:
            break

    if node.color_received is None or node.depth_received is None:
        node.get_logger().error("Did not receive both color and depth in time.")
        node.destroy_node()
        rclpy.shutdown()
        return 1

    color_path = os.path.join(node.out_dir, "ros_color.png")
    depth_path = os.path.join(node.out_dir, "ros_depth.png")
    cv2.imwrite(color_path, node.color_received)
    depth_colormap = cv2.applyColorMap(
        cv2.convertScaleAbs(node.depth_received, alpha=0.03),
        cv2.COLORMAP_JET
    )
    cv2.imwrite(depth_path, depth_colormap)

    print(f"Color: {color_path} shape={node.color_received.shape} stamp={node.color_ts}")
    print(f"Depth: {depth_path} shape={node.depth_received.shape} stamp={node.depth_ts}")

    node.destroy_node()
    rclpy.shutdown()
    return 0


if __name__ == "__main__":
    sys.exit(main())
