import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image


class DepthInspector(Node):
    def __init__(self):
        super().__init__("depth_inspector")
        self.count = 0
        self.create_subscription(Image, "/camera/camera/depth/image_rect_raw", self.callback, 10)

    def callback(self, msg: Image):
        self.count += 1
        if self.count % 20 == 0:
            self.get_logger().info(f"depth image: {msg.width}x{msg.height}, frame_id={msg.header.frame_id}, encoding={msg.encoding}")


def main(args=None):
    rclpy.init(args=args)
    node = DepthInspector()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
