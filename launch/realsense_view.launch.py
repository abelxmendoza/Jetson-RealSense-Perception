from launch import LaunchDescription
from launch.actions import ExecuteProcess


def generate_launch_description():
    return LaunchDescription([
        ExecuteProcess(
            cmd=["ros2", "launch", "realsense2_camera", "rs_launch.py", "enable_color:=true", "enable_depth:=true", "enable_sync:=true"],
            output="screen",
        )
    ])
