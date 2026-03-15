import time

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image


class FrameLatencyCheck(Node):
    def __init__(self):
        super().__init__("frame_latency_check")
        self.last_timestamp = None
        self.count = 0
        self.create_subscription(Image, "/camera/camera/color/image_raw", self.callback, 10)

    def callback(self, msg: Image):
        self.count += 1
        stamp = msg.header.stamp.sec + msg.header.stamp.nanosec * 1e-9

        if self.last_timestamp is not None:
            latency = (time.time() - stamp) * 1000.0
            if self.count % 30 == 0:
                self.get_logger().info(f"frame latency ~ {latency:.1f} ms")

        self.last_timestamp = stamp


def main(args=None):
    rclpy.init(args=args)
    node = FrameLatencyCheck()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
