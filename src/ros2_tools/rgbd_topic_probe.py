#!/usr/bin/env python3
"""ROS2 RGB-D topic probe node.

A lightweight starter node for downstream perception workflows. Subscribes to
color image, depth image, and color camera_info from realsense2_camera.
"""

import time

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import CameraInfo, Image


class RGBDTopicProbe(Node):
    def __init__(self):
        super().__init__("rgbd_topic_probe")

        self._color_count = 0
        self._depth_count = 0
        self._info_count = 0
        self._last_log_time = time.time()

        self._info = None

        self.create_subscription(
            Image,
            "/camera/camera/color/image_raw",
            self._on_color_image,
            10,
        )

        self.create_subscription(
            Image,
            "/camera/camera/depth/image_rect_raw",
            self._on_depth_image,
            10,
        )

        self.create_subscription(
            CameraInfo,
            "/camera/camera/color/camera_info",
            self._on_camera_info,
            10,
        )

        self.get_logger().info("RGBD Topic Probe started. Waiting for messages...")

    def _on_color_image(self, msg: Image):
        self._color_count += 1
        if self._should_log(self._color_count):
            self.get_logger().info(
                f"color image #{self._color_count}: width={msg.width}, height={msg.height}, frame_id={msg.header.frame_id}"
            )

    def _on_depth_image(self, msg: Image):
        self._depth_count += 1
        if self._should_log(self._depth_count):
            self.get_logger().info(
                f"depth image #{self._depth_count}: width={msg.width}, height={msg.height}, frame_id={msg.header.frame_id}"
            )

    def _on_camera_info(self, msg: CameraInfo):
        self._info_count += 1
        if self._should_log(self._info_count):
            self.get_logger().info(
                f"camera_info #{self._info_count}: width={msg.width}, height={msg.height}, frame_id={msg.header.frame_id}"
            )
        if self._info_count == 1:
            self._info = msg

    def _should_log(self, count: int) -> bool:
        # Log first 5 messages, then every 25 messages to avoid spam.
        if count <= 5:
            return True
        if count % 25 == 0:
            now = time.time()
            if now - self._last_log_time > 2.0:
                self._last_log_time = now
                return True
        return False


def main(args=None):
    rclpy.init(args=args)
    node = RGBDTopicProbe()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        node.get_logger().info("Shutting down RGBD Topic Probe")
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
