from launch import LaunchDescription
from launch.actions import ExecuteProcess


def generate_launch_description():
    return LaunchDescription([
        ExecuteProcess(
            cmd=["ros2", "bag", "record", "/camera/camera/color/image_raw", "/camera/camera/depth/image_rect_raw", "/tf"],
            output="screen",
        )
    ])
