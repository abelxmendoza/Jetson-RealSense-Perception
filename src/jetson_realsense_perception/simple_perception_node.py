import time

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image


class SimplePerceptionNode(Node):
    def __init__(self):
        super().__init__("simple_perception_node")
        self.last_time = time.time()
        self.count = 0

        self.create_subscription(Image, "/camera/camera/color/image_raw", self.image_cb, 10)

    def image_cb(self, msg: Image):
        self.count += 1
        now = time.time()
        elapsed = now - self.last_time

        if elapsed >= 1.0:
            self.get_logger().info(f"color fps: {self.count / elapsed:.2f}, resolution: {msg.width}x{msg.height}")
            self.count = 0
            self.last_time = now


def main(args=None):
    rclpy.init(args=args)
    node = SimplePerceptionNode()

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        node.get_logger().info("Shutting down simple_perception_node")
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
