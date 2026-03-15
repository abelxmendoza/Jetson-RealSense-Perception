from launch import LaunchDescription
from launch.actions import ExecuteProcess


def generate_launch_description():
    return LaunchDescription([
        ExecuteProcess(
            cmd=["ros2", "launch", "realsense2_camera", "rs_launch.py", "enable_color:=true", "enable_depth:=true", "enable_sync:=true"],
            output="screen",
        ),
        ExecuteProcess(
            cmd=["ros2", "launch", "foxglove_bridge", "foxglove_bridge_launch.xml", "port:=8765"],
            output="screen",
        ),
        ExecuteProcess(
            cmd=["ros2", "run", "rviz2", "rviz2", "-d", "$(pwd)/rviz/perception.rviz"],
            output="screen",
        ),
    ])
