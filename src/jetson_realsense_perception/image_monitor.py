import time

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image


class ImageMonitor(Node):
    def __init__(self):
        super().__init__("image_monitor")
        self.count = 0
        self.last = time.time()

        self.create_subscription(Image, "/camera/camera/color/image_raw", self.callback, 10)

    def callback(self, msg: Image):
        self.count += 1
        if self.count % 30 == 0:
            interval = time.time() - self.last
            fps = 30.0 / max(interval, 1e-3)
            self.get_logger().info(f"color image: {msg.width}x{msg.height}, frame_id={msg.header.frame_id}, fps={fps:.2f}")
            self.last = time.time()


def main(args=None):
    rclpy.init(args=args)
    node = ImageMonitor()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
